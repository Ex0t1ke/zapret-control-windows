import time
import socket
import ssl
import urllib.request
import threading
from dataclasses import dataclass
from typing import Callable, Optional
from presets_data import PRESETS
from engine import ZapretEngine

# Key targets for checking DPI bypass
TARGETS = [
    {
        "id": "youtube_main",
        "name": "YouTube Web",
        "url": "https://www.youtube.com",
        "type": "http"
    },
    {
        "id": "youtube_video",
        "name": "YouTube Video Stream (16-32KB)",
        "url": "https://redirector.googlevideo.com/videoplayback?id=test",
        "type": "stream_chunk"
    },
    {
        "id": "discord_main",
        "name": "Discord Web",
        "url": "https://discord.com",
        "type": "http"
    },
    {
        "id": "discord_gateway",
        "name": "Discord Gateway",
        "url": "https://gateway.discord.gg",
        "type": "http"
    },
    {
        "id": "discord_cdn",
        "name": "Discord CDN",
        "url": "https://cdn.discordapp.com",
        "type": "http"
    }
]

@dataclass
class TargetResult:
    target_id: str
    target_name: str
    success: bool
    latency_ms: int
    error: str = ""
    bytes_read: int = 0

@dataclass
class PresetBenchmarkResult:
    preset_id: str
    preset_title: str
    success_count: int
    total_count: int
    avg_latency_ms: int
    details: list[TargetResult]
    is_working: bool

class StrategyTester:
    def __init__(self, engine: ZapretEngine):
        self.engine = engine
        self._cancel_flag = threading.Event()

    def cancel(self):
        self._cancel_flag.set()

    def test_single_target(self, target: dict, timeout: float = 3.5) -> TargetResult:
        """Tests accessibility and chunk transfer for a specific target."""
        name = target["name"]
        tid = target["id"]
        url = target["url"]
        target_type = target.get("type", "http")

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
            "Accept": "*/*"
        }

        if target_type == "stream_chunk":
            headers["Range"] = "bytes=0-32768"

        req = urllib.request.Request(url, headers=headers)
        start_time = time.time()

        try:
            # We use an SSL context with standard verification
            ctx = ssl.create_default_context()
            with urllib.request.urlopen(req, timeout=timeout, context=ctx) as response:
                total_bytes = 0
                chunk_start = time.time()
                while total_bytes < 32768:
                    chunk = response.read(8192)
                    if not chunk:
                        break
                    total_bytes += len(chunk)
                    # If reading stalls past 2.5s, likely DPI freeze
                    if time.time() - chunk_start > 2.5 and total_bytes < 16384:
                        return TargetResult(
                            target_id=tid,
                            target_name=name,
                            success=False,
                            latency_ms=int((time.time() - start_time) * 1000),
                            error="DPI Freeze (>16KB stall)",
                            bytes_read=total_bytes
                        )

                latency = int((time.time() - start_time) * 1000)
                return TargetResult(
                    target_id=tid,
                    target_name=name,
                    success=True,
                    latency_ms=latency,
                    bytes_read=total_bytes
                )
        except urllib.error.HTTPError as e:
            # 204, 302, 403, 404 still means TCP/TLS handshake succeeded past DPI!
            latency = int((time.time() - start_time) * 1000)
            if e.code in (200, 204, 206, 301, 302, 304, 400, 403, 404):
                return TargetResult(
                    target_id=tid,
                    target_name=name,
                    success=True,
                    latency_ms=latency,
                    bytes_read=0
                )
            return TargetResult(
                target_id=tid,
                target_name=name,
                success=False,
                latency_ms=latency,
                error=f"HTTP {e.code}"
            )
        except Exception as e:
            latency = int((time.time() - start_time) * 1000)
            err_msg = str(e)
            if "timed out" in err_msg.lower():
                err_msg = "Таймаут (DPI блок)"
            elif "connection reset" in err_msg.lower() or "10054" in err_msg:
                err_msg = "TCP RST (Сброс ТСПУ)"
            return TargetResult(
                target_id=tid,
                target_name=name,
                success=False,
                latency_ms=latency,
                error=err_msg
            )

    def test_current_connection(self, on_target_finished: Optional[Callable[[TargetResult], None]] = None) -> list[TargetResult]:
        """Runs test on all targets with the currently running configuration."""
        results = []
        for target in TARGETS:
            if self._cancel_flag.is_set():
                break
            res = self.test_single_target(target)
            results.append(res)
            if on_target_finished:
                on_target_finished(res)
        return results

    def benchmark_presets(
        self,
        preset_ids: list[str],
        progress_callback: Optional[Callable[[int, int, str, PresetBenchmarkResult], None]] = None
    ) -> list[PresetBenchmarkResult]:
        """
        Sequentially runs winws.exe with each preset, tests targets, and ranks results.
        Restores original state afterwards.
        """
        self._cancel_flag.clear()
        initial_running = self.engine.is_process_running()
        initial_preset = self.engine.config.get("active_preset", "general")
        benchmark_results = []

        total = len(preset_ids)

        try:
            for idx, pid in enumerate(preset_ids):
                if self._cancel_flag.is_set():
                    break

                preset_info = PRESETS.get(pid, {"title": pid})
                title = preset_info.get("title", pid)

                # Restart winws with this preset
                self.engine.start_process(preset_id=pid)
                # Wait 1.0s for winws & WinDivert to bind network adapter
                time.sleep(1.0)

                # Test critical targets (YouTube stream chunk + Discord gateway)
                details = []
                # First test YouTube Stream & Discord
                test_targets = [
                    TARGETS[1], # YouTube stream chunk
                    TARGETS[0], # YouTube web
                    TARGETS[3]  # Discord gateway
                ]

                latencies = []
                success_count = 0

                for t in test_targets:
                    if self._cancel_flag.is_set():
                        break
                    res = self.test_single_target(t, timeout=3.0)
                    details.append(res)
                    if res.success:
                        success_count += 1
                        latencies.append(res.latency_ms)

                avg_lat = int(sum(latencies) / len(latencies)) if latencies else 9999
                is_working = success_count >= 2  # at least YouTube and Discord passed

                bench_res = PresetBenchmarkResult(
                    preset_id=pid,
                    preset_title=title,
                    success_count=success_count,
                    total_count=len(test_targets),
                    avg_latency_ms=avg_lat,
                    details=details,
                    is_working=is_working
                )

                benchmark_results.append(bench_res)

                if progress_callback:
                    progress_callback(idx + 1, total, title, bench_res)

        finally:
            # Restore state
            if initial_running:
                self.engine.start_process(preset_id=initial_preset)
            else:
                self.engine.stop_process()

        # Sort results: working first, then by success count (descending), then by latency (ascending)
        benchmark_results.sort(
            key=lambda r: (not r.is_working, -r.success_count, r.avg_latency_ms)
        )
        return benchmark_results
