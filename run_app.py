import os
import sys
import time
import webview
from pathlib import Path

from engine import ZapretEngine, is_admin, restart_as_admin, LISTS_DIR
from tester import StrategyTester
from presets_data import PRESETS

BASE_DIR = Path(__file__).resolve().parent

def get_dist_dir() -> Path:
    if getattr(sys, 'frozen', False):
        exe_dir = Path(sys.executable).resolve().parent
        if (exe_dir / "extracted_interface" / "dist" / "index.html").exists():
            return exe_dir / "extracted_interface" / "dist"
        if hasattr(sys, '_MEIPASS'):
            mei_dir = Path(sys._MEIPASS).resolve()
            if (mei_dir / "extracted_interface" / "dist" / "index.html").exists():
                return mei_dir / "extracted_interface" / "dist"
        if (exe_dir / "ui" / "index.html").exists():
            return exe_dir / "ui"
    return BASE_DIR / "extracted_interface" / "dist"

DIST_DIR = get_dist_dir()
INDEX_HTML = DIST_DIR / "index.html"

class WebviewAPI:
    def __init__(self, engine: ZapretEngine, tester: StrategyTester):
        self.engine = engine
        self.tester = tester
        self.log_entries = []
        self._next_log_id = 1
        self.engine.log_callback = self._on_log

    def _on_log(self, message: str, level: str):
        t_str = time.strftime("%H:%M:%S")
        entry = {
            "id": self._next_log_id,
            "time": t_str,
            "message": f"[{level}] {message}"
        }
        self._next_log_id += 1
        self.log_entries.append(entry)
        if len(self.log_entries) > 200:
            self.log_entries = self.log_entries[-200:]

    def get_initial_state(self):
        # Read user domains from list-general-user.txt
        user_list = LISTS_DIR / "list-general-user.txt"
        domains = []
        if user_list.exists():
            try:
                with open(user_list, "r", encoding="utf-8", errors="ignore") as f:
                    domains = [l.strip() for l in f if l.strip() and not l.startswith("#")]
            except Exception:
                pass
        if not domains:
            domains = ["youtube.com", "discord.com", "googlevideo.com"]

        active = self.engine.is_process_running()
        srv_status = self.engine.get_service_status()

        return {
            "active": active or (srv_status == "running"),
            "preset": self.engine.config.get("active_preset", "general"),
            "gameMode": self.engine.config.get("game_filter", "disabled"),
            "serviceInstalled": (srv_status == "running"),
            "isAdmin": is_admin(),
            "domains": domains,
            "logs": list(reversed(self.log_entries[-30:]))
        }

    def start_protection(self, presetId=None):
        pid = presetId or self.engine.config.get("active_preset", "general")
        return self.engine.start_process(pid)

    def stop_protection(self):
        return self.engine.stop_process()

    def set_preset(self, presetId):
        self.engine.config.set("active_preset", presetId)
        if self.engine.is_process_running():
            return self.engine.start_process(presetId)
        return True

    def set_game_filter(self, mode):
        self.engine.config.set("game_filter", mode)
        if self.engine.is_process_running():
            return self.engine.start_process()
        return True

    def install_service(self):
        if not is_admin():
            return False
        if self.engine.is_process_running():
            self.engine.stop_process()
        return self.engine.install_service()

    def uninstall_service(self):
        if not is_admin():
            return False
        return self.engine.uninstall_service()

    def check_availability(self):
        results = self.tester.test_current_connection()
        count_ok = sum(1 for r in results if r.success)
        details = [
            {
                "name": r.target_name,
                "success": r.success,
                "latency_ms": r.latency_ms,
                "error": r.error
            }
            for r in results
        ]
        return {
            "count_ok": count_ok,
            "total": len(results),
            "details": details
        }

    def run_benchmark(self):
        candidates = [
            "general",
            "general (ALT)",
            "general (ALT2)",
            "general (ALT4)",
            "general (ALT6)",
            "general (ALT10)",
            "general (ALT11)",
            "general (FAKE TLS AUTO)",
            "general (SIMPLE FAKE)"
        ]
        results = self.tester.benchmark_presets(candidates)
        recommended = "general (ALT)"
        working = [r for r in results if r.is_working]
        if working:
            recommended = working[0].preset_id

        res_list = [
            {
                "preset_id": r.preset_id,
                "preset_title": r.preset_title,
                "success_count": r.success_count,
                "total_count": r.total_count,
                "avg_latency_ms": r.avg_latency_ms,
                "is_working": r.is_working
            }
            for r in results
        ]
        return {
            "recommended": recommended,
            "results": res_list
        }

    def get_domains(self):
        user_list = LISTS_DIR / "list-general-user.txt"
        if user_list.exists():
            with open(user_list, "r", encoding="utf-8", errors="ignore") as f:
                return [l.strip() for l in f if l.strip() and not l.startswith("#")]
        return []

    def add_domain(self, domain):
        user_list = LISTS_DIR / "list-general-user.txt"
        try:
            with open(user_list, "a", encoding="utf-8") as f:
                f.write(f"\n{domain.strip()}")
            if self.engine.is_process_running():
                self.engine.start_process()
            return True
        except Exception:
            return False

    def remove_domain(self, domain):
        user_list = LISTS_DIR / "list-general-user.txt"
        try:
            if user_list.exists():
                with open(user_list, "r", encoding="utf-8", errors="ignore") as f:
                    lines = [l.strip() for l in f if l.strip() and l.strip() != domain.strip()]
                with open(user_list, "w", encoding="utf-8") as f:
                    f.write("\n".join(lines) + "\n")
                if self.engine.is_process_running():
                    self.engine.start_process()
            return True
        except Exception:
            return False

    def clear_logs(self):
        self.log_entries.clear()
        return True

    def restart_as_admin(self):
        restart_as_admin()

def main():
    if not INDEX_HTML.exists():
        print(f"Error: {INDEX_HTML} not found. Please build the frontend first.")
        return

    engine = ZapretEngine()
    tester = StrategyTester(engine)
    api = WebviewAPI(engine, tester)

    window = webview.create_window(
        title="Zapret Desktop Control",
        url=str(INDEX_HTML),
        js_api=api,
        width=1120,
        height=760,
        min_size=(900, 650),
        background_color="#0d0d0e"
    )

    def on_closed():
        # Stop process if not service mode
        if engine.get_service_status() != "running":
            engine.stop_process()

    window.events.closed += on_closed
    webview.start(debug=False)

if __name__ == "__main__":
    main()
