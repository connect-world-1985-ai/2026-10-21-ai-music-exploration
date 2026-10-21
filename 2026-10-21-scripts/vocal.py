"""'Poor man's vocal synth': eSpeak-NG formant TTS turned into singing.
Per syllable: render with SSML <prosody range="x-low"> (flattens speech intonation) ->
pYIN f0 estimate -> librosa pitch-shift to the target MIDI note -> split into
consonant onset / voiced nucleus / coda and time-stretch only the voiced nucleus to the
note length -> delayed vibrato (modulated delay line) -> amplitude envelope."""
import os, subprocess, tempfile, functools
import numpy as np, librosa
from common import SR, mtof

@functools.lru_cache(maxsize=None)
def _tts(text, voice, speed):
    with tempfile.TemporaryDirectory() as d:
        ssml = os.path.join(d, "s.ssml"); wav = os.path.join(d, "s.wav")
        open(ssml, "w").write(f'<speak><prosody range="x-low">{text}</prosody></speak>')
        subprocess.run(["espeak-ng", "-m", "-v", voice, "-s", str(speed), "-w", wav, "-f", ssml], check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        y, sr = librosa.load(wav, sr=SR)
    y, _ = librosa.effects.trim(y, top_db=35)
    return y

def sing_note(text, midi, dur, voice="en-us+f3", speed=120, vib_depth=0.35, vib_rate=5.3):
    y = _tts(text, voice, speed).copy()
    hop = 256
    f0, vflag, _ = librosa.pyin(y, fmin=70, fmax=600, sr=SR, frame_length=2048, hop_length=hop)
    voiced = np.where(vflag)[0]
    target = float(mtof(midi)); n_target = int(dur * SR)
    if len(voiced) < 2:   # unvoiced syllable: just pad/cut
        out = np.zeros(n_target); out[:min(len(y), n_target)] = y[:n_target]; return out
    med = np.nanmedian(f0[voiced])
    y = librosa.effects.pitch_shift(y, sr=SR, n_steps=12 * np.log2(target / med), bins_per_octave=12)
    a, b = voiced[0] * hop, min(len(y), (voiced[-1] + 1) * hop)
    pre, nuc, post = y[:a], y[a:b], y[b:]
    room = max(n_target - len(pre) - len(post), int(0.05 * SR))
    rate = np.clip(len(nuc) / room, 0.08, 4.0)
    nuc = librosa.effects.time_stretch(nuc, rate=rate)
    out = np.concatenate([pre, nuc, post])
    # delayed-onset vibrato via modulated fractional delay
    t = np.arange(len(out)) / SR
    depth_s = (2 ** (vib_depth / 12) - 1) / (2 * np.pi * vib_rate)
    d = depth_s * SR * np.sin(2 * np.pi * vib_rate * t) * np.clip((t - 0.25) / 0.4, 0, 1)
    out = np.interp(np.arange(len(out)) - d - 40, np.arange(len(out)), out, left=0)
    n = len(out); fi, fo = min(int(.01 * SR), n), min(int(.06 * SR), n)
    out[:fi] *= np.linspace(0, 1, fi); out[n - fo:] *= np.linspace(1, 0, fo)
    return out[: max(n_target, 1)] if len(out) > n_target * 1.15 else out

def sing(events, buf_len, **kw):
    """events: list of (syllable, midi, start_s, dur_s). Returns mono buffer."""
    buf = np.zeros(buf_len)
    for text, m, st, du in events:
        x = sing_note(text, m, du, **kw); i = int(st * SR); x = x[: buf_len - i]
        buf[i:i + len(x)] += x / (np.max(np.abs(x)) + 1e-9)
    return buf
