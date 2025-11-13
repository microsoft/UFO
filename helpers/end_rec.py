# end_record.py
import json, os, signal, tempfile, time
from pathlib import Path
import subprocess

PID_FILE = Path(tempfile.gettempdir()) / "screenrec_ffmpeg.pid"
META_FILE = Path(tempfile.gettempdir()) / "screenrec_meta.json"

def main():
    if not PID_FILE.exists():
        raise SystemExit("No active recording found (pid file missing).")

    pid = int(PID_FILE.read_text().strip())
    meta = {}
    if META_FILE.exists():
        try:
            meta = json.loads(META_FILE.read_text(encoding="utf-8"))
        except Exception:
            meta = {}

    # Send CTRL_BREAK_EVENT so FFmpeg finalizes the MP4 (like Ctrl+C)
    try:
        os.kill(pid, signal.CTRL_BREAK_EVENT)
    except Exception as e:
        print(f"CTRL_BREAK failed: {e}. Falling back to terminate...")
        try:
            # Last resort: hard terminate (may produce unplayable MP4)
            subprocess.run(["taskkill", "/PID", str(pid), "/T", "/F"], check=False)
        except Exception as e2:
            print(f"taskkill failed: {e2}")

    # Give FFmpeg a moment to flush and close
    time.sleep(2)

    # Cleanup
    if PID_FILE.exists():
        PID_FILE.unlink(missing_ok=True)

    out = meta.get("out", "<unknown file>")
    print(f"Recording stopped. File saved to:\n{out}")

    if META_FILE.exists():
        META_FILE.unlink(missing_ok=True)

if __name__ == "__main__":
    main()
