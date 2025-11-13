# record.py
import argparse, datetime as dt, json, os, signal, subprocess, tempfile, time
from pathlib import Path

FFMPEG = "ffmpeg"  # or r"C:\ffmpeg\bin\ffmpeg.exe"
PID_FILE = Path(tempfile.gettempdir()) / "screenrec_ffmpeg.pid"
META_FILE = Path(tempfile.gettempdir()) / "screenrec_meta.json"

def default_output():
    ts = dt.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    videos = Path.home() / "Videos"
    videos.mkdir(parents=True, exist_ok=True)
    return videos / f"screen_{ts}.mp4"

def main():
    ap = argparse.ArgumentParser(description="Start screen recording (Windows).")
    ap.add_argument("--out", type=Path, default=default_output(),
                    help="Output MP4 file path (default: ~/Videos/screen_YYYY-mm-dd_HH-MM-SS.mp4)")
    ap.add_argument("--fps", type=int, default=30, help="Frame rate (default: 30)")
    ap.add_argument("--cursor", action="store_true", help="Show cursor (for gdigrab only)")
    ap.add_argument("--grab", choices=["ddagrab","gdigrab"], default="ddagrab",
                    help="Windows screen grabber (default: ddagrab; use gdigrab for older Windows)")
    args = ap.parse_args()

    if PID_FILE.exists():
        raise SystemExit(f"Recording already in progress (pid file exists at {PID_FILE}). "
                         f"Run end_record.py first.")

    # Build FFmpeg input(s)
    # Video (whole desktop)
    if args.grab == "ddagrab":
        video_in = ["-f","ddagrab","-framerate",str(args.fps),"-i","desktop"]
    else:
        # gdigrab supports cursor toggle
        video_in = ["-f","gdigrab","-framerate",str(args.fps),"-i","desktop"]
        if args.cursor:
            video_in = ["-f","gdigrab","-framerate",str(args.fps),"-draw_mouse","1","-i","desktop"]

    # Output settings: H.264, faststart for web playback
    out = str(args.out)
    cmd = [
        FFMPEG, "-y",
        *video_in,
        "-pix_fmt","yuv420p",
        "-c:v","libx264","-preset","veryfast","-crf","23",
        "-movflags","+faststart",
        out
    ]

    # Start FFmpeg in its own process group so we can send CTRL_BREAK_EVENT later
    creationflags = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
    # Open with its own console I/O so it can receive the control event:
    proc = subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        creationflags=creationflags
    )

    # Persist pid + meta so end_record.py can stop it and report
    PID_FILE.write_text(str(proc.pid), encoding="utf-8")
    META_FILE.write_text(json.dumps({"out": out, "started": time.time(), "grab": args.grab}, ensure_ascii=False))

    print(f"Recording started (PID {proc.pid}). Writing to:\n{out}\n"
          f"To stop: python end_record.py")

if __name__ == "__main__":
    main()
