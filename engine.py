import os
import sys
import ctypes
import json
import shlex
import subprocess
import threading
import queue
import time
from pathlib import Path
from presets_data import PRESETS

def get_app_dir() -> Path:
    """Robustly resolve base application directory in both dev and PyInstaller modes."""
    # 1. Check parent of sys.executable (for onedir PyInstaller next to .exe)
    if getattr(sys, 'frozen', False):
        exe_dir = Path(sys.executable).resolve().parent
        if (exe_dir / "bin" / "winws.exe").exists():
            return exe_dir
        if hasattr(sys, '_MEIPASS'):
            mei_dir = Path(sys._MEIPASS).resolve()
            if (mei_dir / "bin" / "winws.exe").exists():
                return mei_dir

    # 2. Check parent of __file__ (normal Python or _internal folder)
    file_dir = Path(__file__).resolve().parent
    if (file_dir / "bin" / "winws.exe").exists():
        return file_dir

    # 3. Check parent of file_dir (e.g. if __file__ is in _internal)
    if (file_dir.parent / "bin" / "winws.exe").exists():
        return file_dir.parent

    # 4. Fallback to current working directory
    cwd = Path.cwd().resolve()
    if (cwd / "bin" / "winws.exe").exists():
        return cwd

    return file_dir

BASE_DIR = get_app_dir()
BIN_DIR = BASE_DIR / "bin"
LISTS_DIR = BASE_DIR / "lists"
CONFIG_FILE = BASE_DIR / "config.json"
WINWS_EXE = BIN_DIR / "winws.exe"

def is_admin() -> bool:
    """Check if the current process has administrator rights."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        return False

def restart_as_admin():
    """Relaunches the current python script or executable with admin elevation."""
    if is_admin():
        return
    params = " ".join([f'"{arg}"' for arg in sys.argv])
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, params, None, 1)
    sys.exit(0)

class ConfigManager:
    DEFAULT_CONFIG = {
        "active_preset": "general",
        "game_filter": "disabled",  # "disabled", "both", "tcp", "udp"
        "custom_args": "",
        "autostart": False,
        "minimize_to_tray": True,
        "mode": "process"  # "process" or "service"
    }

    def __init__(self, path: Path = CONFIG_FILE):
        self.path = path
        self.data = dict(self.DEFAULT_CONFIG)
        self.load()

    def load(self):
        if self.path.exists():
            try:
                with open(self.path, "r", encoding="utf-8") as f:
                    saved = json.load(f)
                    self.data.update(saved)
            except Exception as e:
                print(f"Error loading config: {e}")

    def save(self):
        try:
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving config: {e}")

    def get(self, key, default=None):
        return self.data.get(key, default)

    def set(self, key, value):
        self.data[key] = value
        self.save()

class ZapretEngine:
    def __init__(self, log_callback=None):
        self.config = ConfigManager()
        self.log_callback = log_callback
        self.process: subprocess.Popen = None
        self._output_queue = queue.Queue()
        self._reader_thread = None
        self._stop_event = threading.Event()

    def log(self, message: str, level: str = "INFO"):
        formatted = f"[{time.strftime('%H:%M:%S')}] [{level}] {message}"
        print(formatted)
        if self.log_callback:
            try:
                self.log_callback(formatted, level)
            except Exception:
                pass

    def get_game_filter_ports(self, mode: str = None) -> tuple[str, str]:
        """Returns (GameFilterTCP, GameFilterUDP) based on game filter mode."""
        if mode is None:
            mode = self.config.get("game_filter", "disabled")
        
        if mode == "both":
            return ("1024-65535", "1024-65535")
        elif mode == "tcp":
            return ("1024-65535", "12")
        elif mode == "udp":
            return ("12", "1024-65535")
        else:  # disabled
            return ("12", "12")

    def build_command_args(self, preset_id: str = None, game_filter_mode: str = None) -> list[str]:
        """Builds resolved arguments list for winws.exe."""
        if not preset_id:
            preset_id = self.config.get("active_preset", "general")
        
        if preset_id == "custom":
            raw_args = self.config.get("custom_args", "")
            return shlex.split(raw_args, posix=False)

        preset = PRESETS.get(preset_id)
        if not preset:
            preset = PRESETS["general"]

        tokens = preset.get("tokens", [])
        tcp_port, udp_port = self.get_game_filter_ports(game_filter_mode)

        bin_str = str(BIN_DIR) + "\\"
        lists_str = str(LISTS_DIR) + "\\"

        resolved_args = []
        for token in tokens:
            t = token
            # Strip external quotes from values like --hostlist="path" -> --hostlist=path
            if '="' in t and t.endswith('"'):
                prefix, val = t.split('="', 1)
                val = val[:-1]
                t = f"{prefix}={val}"
            elif t.startswith('"') and t.endswith('"'):
                t = t[1:-1]

            # Replace variable tokens
            t = t.replace("%BIN%", bin_str).replace("%LISTS%", lists_str)
            t = t.replace("%GameFilterTCP%", tcp_port).replace("%GameFilterUDP%", udp_port)
            resolved_args.append(t)

        return resolved_args

    def is_process_running(self) -> bool:
        """Check if winws.exe process is currently active."""
        if self.process and self.process.poll() is None:
            return True
        # Check system-wide if winws.exe is running
        try:
            output = subprocess.check_output(
                ["tasklist", "/FI", "IMAGENAME eq winws.exe", "/NH"],
                creationflags=subprocess.CREATE_NO_WINDOW,
                text=True,
                errors="ignore"
            )
            return "winws.exe" in output.lower()
        except Exception:
            return False

    def kill_existing_winws(self):
        """Forcefully kills any orphan winws.exe processes."""
        try:
            subprocess.run(
                ["taskkill", "/F", "/IM", "winws.exe"],
                creationflags=subprocess.CREATE_NO_WINDOW,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        except Exception:
            pass

    def start_process(self, preset_id: str = None) -> bool:
        """Starts winws.exe with specified or configured preset."""
        if not WINWS_EXE.exists():
            self.log(f"winws.exe не найден по пути: {WINWS_EXE}", "ERROR")
            return False

        if self.is_process_running():
            self.log("winws.exe уже запущен. Завершаем предыдущие копии...", "WARNING")
            self.stop_process()
            time.sleep(0.5)

        preset = PRESETS.get(preset_id or self.config.get("active_preset", "general"), {})
        title = preset.get("title", preset_id or "Custom")
        args = self.build_command_args(preset_id)

        cmd = [str(WINWS_EXE)] + args
        self.log(f"Запуск winws.exe [{title}]...", "INFO")

        try:
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                stdin=subprocess.DEVNULL,
                text=True,
                encoding="utf-8",
                errors="replace",
                creationflags=subprocess.CREATE_NO_WINDOW,
                cwd=str(BIN_DIR)
            )

            # Start background reader thread
            self._stop_event.clear()
            self._reader_thread = threading.Thread(target=self._read_output, daemon=True)
            self._reader_thread.start()

            time.sleep(0.4)
            if self.process.poll() is not None:
                ret = self.process.returncode
                self.log(f"winws.exe аварийно завершился с кодом {ret}. (Возможно, требуется запуск от Администратора)", "ERROR")
                return False

            self.log(f"Процесс winws.exe успешно запущен (PID {self.process.pid}). Защита активна!", "SUCCESS")
            return True

        except Exception as e:
            self.log(f"Ошибка при запуске winws.exe: {e}", "ERROR")
            return False

    def stop_process(self) -> bool:
        """Stops winws.exe process."""
        self.log("Остановка winws.exe...", "INFO")
        self._stop_event.set()
        
        if self.process and self.process.poll() is None:
            try:
                self.process.terminate()
                self.process.wait(timeout=2.0)
            except Exception:
                pass
        
        self.kill_existing_winws()
        self.process = None
        self.log("winws.exe остановлен.", "INFO")
        return True

    def _read_output(self):
        """Worker thread to capture stdout/stderr from winws.exe."""
        if not self.process or not self.process.stdout:
            return
        
        while not self._stop_event.is_set():
            line = self.process.stdout.readline()
            if not line:
                if self.process.poll() is not None:
                    break
                time.sleep(0.05)
                continue
            
            clean_line = line.strip()
            if clean_line:
                level = "INFO"
                if "error" in clean_line.lower() or "failed" in clean_line.lower():
                    level = "ERROR"
                elif "warn" in clean_line.lower():
                    level = "WARNING"
                self.log(clean_line, level)

    # ========================================================
    # Windows Service Management
    # ========================================================
    def get_service_status(self) -> str:
        """
        Returns:
            'running' - service is installed and running
            'stopped' - service is installed but stopped
            'not_installed' - service does not exist
        """
        try:
            res = subprocess.run(
                ["sc", "query", "zapret"],
                creationflags=subprocess.CREATE_NO_WINDOW,
                capture_output=True,
                text=True,
                errors="ignore"
            )
            if res.returncode != 0 or "1060" in res.stderr or "FAILED 1060" in res.stdout:
                return "not_installed"
            if "RUNNING" in res.stdout:
                return "running"
            return "stopped"
        except Exception:
            return "not_installed"

    def install_service(self, preset_id: str = None) -> bool:
        """Registers and starts winws.exe as a Windows Service."""
        if not is_admin():
            self.log("Установка службы требует прав Администратора!", "ERROR")
            return False

        if not WINWS_EXE.exists():
            self.log(f"winws.exe не найден: {WINWS_EXE}", "ERROR")
            return False

        preset = PRESETS.get(preset_id or self.config.get("active_preset", "general"), {})
        title = preset.get("title", preset_id or "Custom")
        args_list = self.build_command_args(preset_id)
        
        # In sc create binPath, winws.exe and arguments must be properly formatted
        joined_args = " ".join([f'"{a}"' if ' ' in a else a for a in args_list])
        bin_path_str = f'"{WINWS_EXE}" {joined_args}'

        self.log(f"Установка службы Windows 'zapret' [{title}]...", "INFO")

        # First stop & delete any existing service
        self.uninstall_service(silent=True)

        try:
            # sc create zapret binPath= "..." DisplayName= "zapret" start= auto
            cmd_create = [
                "sc", "create", "zapret",
                f"binPath= {bin_path_str}",
                "DisplayName= zapret",
                "start= auto"
            ]
            res = subprocess.run(
                cmd_create,
                creationflags=subprocess.CREATE_NO_WINDOW,
                capture_output=True,
                text=True,
                errors="ignore"
            )
            if res.returncode != 0:
                self.log(f"Не удалось создать службу: {res.stdout} {res.stderr}", "ERROR")
                return False

            # Set description
            subprocess.run(
                ["sc", "description", "zapret", "Zapret DPI bypass service"],
                creationflags=subprocess.CREATE_NO_WINDOW,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )

            # Start service
            cmd_start = ["sc", "start", "zapret"]
            res_start = subprocess.run(
                cmd_start,
                creationflags=subprocess.CREATE_NO_WINDOW,
                capture_output=True,
                text=True,
                errors="ignore"
            )
            if res_start.returncode != 0:
                self.log(f"Служба создана, но запуск не удался: {res_start.stdout} {res_start.stderr}", "WARNING")
            else:
                self.log("Служба zapret успешно установлена и запущена в автозагрузке Windows!", "SUCCESS")

            return True
        except Exception as e:
            self.log(f"Исключение при установке службы: {e}", "ERROR")
            return False

    def uninstall_service(self, silent: bool = False) -> bool:
        """Stops and deletes zapret Windows Service."""
        if not is_admin() and not silent:
            self.log("Удаление службы требует прав Администратора!", "ERROR")
            return False

        try:
            subprocess.run(
                ["net", "stop", "zapret"],
                creationflags=subprocess.CREATE_NO_WINDOW,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            subprocess.run(
                ["sc", "delete", "zapret"],
                creationflags=subprocess.CREATE_NO_WINDOW,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            if not silent:
                self.log("Служба zapret остановлена и удалена.", "INFO")
            return True
        except Exception as e:
            if not silent:
                self.log(f"Ошибка при удалении службы: {e}", "ERROR")
            return False

    def toggle_service(self) -> bool:
        """Starts or stops the already installed service."""
        status = self.get_service_status()
        if status == "running":
            res = subprocess.run(["net", "stop", "zapret"], creationflags=subprocess.CREATE_NO_WINDOW)
            self.log("Служба остановлена.", "INFO")
            return res.returncode == 0
        elif status == "stopped":
            res = subprocess.run(["net", "start", "zapret"], creationflags=subprocess.CREATE_NO_WINDOW)
            self.log("Служба запущена.", "SUCCESS")
            return res.returncode == 0
        return False
