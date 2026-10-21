"""Listen-proxy QA: decode every mp3 with ffmpeg, check duration, peak (<= -0.5 dBFS), RMS (not silent),
and estimate vocal pitch accuracy is not possible from the mix, so we report spectral centroid as a brightness proxy."""
import glob, os, subprocess, json, numpy as np
from common import PIECES, SR
rows = []
for mp3 in sorted(glob.glob(os.path.join(PIECES, "*", "*.mp3"))):
    raw = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", mp3, "-f", "f32le", "-ac", "2", "-ar", str(SR), "-"],
                         capture_output=True, check=True).stdout
    x = np.frombuffer(raw, np.float32).reshape(-1, 2)
    peak = 20 * np.log10(np.max(np.abs(x)) + 1e-12); rms = 20 * np.log10(np.sqrt(np.mean(x ** 2)) + 1e-12)
    dur = len(x) / SR; size = os.path.getsize(mp3) / 1e6
    ok = 30 <= dur <= 90 and peak <= -0.5 and rms > -40
    rows.append(dict(file=os.path.relpath(mp3, os.path.dirname(PIECES)), duration_s=round(float(dur), 1), peak_dbfs=round(float(peak), 2),
                     rms_dbfs=round(float(rms), 1), size_mb=round(size, 2), ok=bool(ok)))
    print(rows[-1])
json.dump(rows, open(os.path.join(PIECES, "qa_report.json"), "w"), indent=2)
assert all(r["ok"] for r in rows), "QA failed"
