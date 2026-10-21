"""Master the raw MusicGen output (32 kHz mono) -> 44.1 kHz, light stereo widening + room, export."""
import sys, numpy as np, soundfile as sf, librosa
from common import *
raw = sys.argv[1] if len(sys.argv) > 1 else "/tmp/musicgen_raw.wav"
y, sr = sf.read(raw); y = librosa.resample(y, orig_sr=sr, target_sr=SR)
st = np.stack([y, np.roll(lowpass(y, 9000), int(0.012 * SR))], 1) * 0.5 + 0.5 * to_stereo(y)
export("2026-10-21-p6-ai-musicgen-late-night-trio", reverb(st, 1.2, 0.1), dict(
    title="Late Night Trio (MusicGen)", style="Smooth jazz piano trio (AI text-to-music)",
    prompt="late night smooth jazz trio, warm upright bass walking line, brushed drums, mellow grand piano chords and melody, intimate club recording, 90 bpm",
    method="facebook/musicgen-small (300M, HF transformers, CPU, seed 2026, guidance 3.0, 1600 tokens) + mastering"))
