"""Shared DSP / rendering / mastering helpers for all pieces."""
import os, subprocess, tempfile, json
import numpy as np
import soundfile as sf
from scipy import signal

SR = 44100
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PIECES = os.path.join(ROOT, "2026-10-21-pieces")
SF2 = "/usr/share/sounds/sf2/FluidR3_GM.sf2"
rng = np.random.default_rng(2026)

def mtof(m):
    return 440.0 * 2 ** ((np.asarray(m, dtype=float) - 69) / 12)

# ---------- oscillators ----------
def _polyblep(t, dt):
    out = np.zeros_like(t); dt = np.broadcast_to(dt, t.shape)
    m = t < dt
    x = t[m] / dt[m]; out[m] = x + x - x * x - 1
    m = t > 1 - dt
    x = (t[m] - 1) / dt[m]; out[m] = x * x + x + x + 1
    return out

def phase_of(freq, n):
    f = np.broadcast_to(np.asarray(freq, dtype=float), (n,))
    return np.cumsum(f / SR) % 1.0, f / SR

def saw(freq, n, ph0=0.0):
    t, dt = phase_of(freq, n); t = (t + ph0) % 1.0
    return 2 * t - 1 - _polyblep(t, dt)

def square(freq, n, pw=0.5):
    t, dt = phase_of(freq, n)
    s = np.where(t < pw, 1.0, -1.0)
    s += _polyblep(t, dt) - _polyblep((t + 1 - pw) % 1.0, dt)
    return s

def sine(freq, n, ph0=0.0):
    t, _ = phase_of(freq, n)
    return np.sin(2 * np.pi * (t + ph0))

def noise(n):
    return rng.standard_normal(n)

def adsr(n, a=0.01, d=0.1, s=0.7, r=0.1):
    a, d, r = int(a * SR), int(d * SR), int(r * SR)
    env = np.full(n, s, dtype=float)
    a = min(a, n); env[:a] = np.linspace(0, 1, a, endpoint=False)
    d2 = min(d, n - a); env[a:a + d2] = np.linspace(1, s, d2, endpoint=False)
    r = min(r, n); env[n - r:] *= np.linspace(1, 0, r)
    return env

# ---------- filters / effects ----------
def lowpass(x, fc, order=2):
    b, a = signal.butter(order, min(fc, SR * 0.45) / (SR / 2), "low"); return signal.lfilter(b, a, x, axis=0)

def highpass(x, fc, order=2):
    b, a = signal.butter(order, fc / (SR / 2), "high"); return signal.lfilter(b, a, x, axis=0)

def bandpass(x, lo, hi, order=2):
    b, a = signal.butter(order, [lo / (SR / 2), hi / (SR / 2)], "band"); return signal.lfilter(b, a, x, axis=0)

def sweep_lowpass(x, fc_curve, block=256):
    """Time-varying 2-pole state-variable lowpass (Chamberlin), fc per sample."""
    y = np.zeros_like(x); low = band = 0.0; q = 0.7
    f = 2 * np.sin(np.pi * np.clip(fc_curve, 20, SR / 6) / SR)
    for i in range(len(x)):
        low += f[i] * band; high = x[i] - low - q * band; band += f[i] * high; y[i] = low
    return y

def reverb(x, seconds=2.0, mix=0.25, predelay=0.02, damp=4000):
    """Stereo convolution reverb using decaying filtered noise IRs."""
    n = int(seconds * SR); t = np.arange(n) / SR
    env = np.exp(-6.9 * t / seconds)
    irs = []
    for _ in range(2):
        ir = noise(n) * env; ir = lowpass(ir, damp); ir[: int(predelay * SR)] = 0
        irs.append(ir / np.sqrt(np.sum(ir ** 2)))
    x = to_stereo(x)
    wet = np.stack([signal.fftconvolve(x[:, c], irs[c])[: len(x)] for c in range(2)], 1)
    return (1 - mix) * x + mix * wet

def delay(x, seconds, fb=0.35, mix=0.3, pingpong=True):
    x = to_stereo(x); d = int(seconds * SR); y = x.copy(); tap = x.copy()
    for k in range(1, 7):
        tap = np.roll(tap, d, axis=0); tap[:d] = 0; tap = tap * fb
        if pingpong: tap = tap[:, ::-1]
        y += tap * mix / fb
    return y

def to_stereo(x):
    return np.stack([x, x], 1) if x.ndim == 1 else x

def pan(x, p):  # p in [-1, 1]
    a = (p + 1) * np.pi / 4
    return np.stack([x * np.cos(a), x * np.sin(a)], 1)

def softclip(x, drive=1.5):
    return np.tanh(x * drive) / np.tanh(drive)

def place(buf, x, start_s):
    i = int(round(start_s * SR))
    if i >= len(buf): return
    x = x[: len(buf) - i]; buf[i:i + len(x)] += x

# ---------- MIDI rendering via FluidSynth ----------
def render_midi(pm, gain=0.8):
    with tempfile.TemporaryDirectory() as d:
        mid = os.path.join(d, "a.mid"); wav = os.path.join(d, "a.wav")
        pm.write(mid)
        subprocess.run(["fluidsynth", "-ni", "-q", "-g", str(gain), "-r", str(SR), "-F", wav, SF2, mid],
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        y, sr = sf.read(wav); assert sr == SR
    return y

def stem(pm_factory, *a, **k):
    return render_midi(pm_factory(*a, **k))

# ---------- mastering / export ----------
def master(x, target_peak_db=-1.0, fade_out=2.0):
    x = to_stereo(np.asarray(x, dtype=float))
    x = x - x.mean(0)
    x = highpass(x, 25)
    # gentle bus compression (RMS-based, slow) then soft clip, then peak normalise
    env = np.sqrt(signal.lfilter([0.001], [1, -0.999], (x ** 2).mean(1)) + 1e-12)
    thr = np.percentile(env, 90) * 0.8
    gain = np.where(env > thr, (thr / env) ** 0.35, 1.0)
    x = x * gain[:, None]
    x = x / (np.max(np.abs(x)) + 1e-12)
    x = softclip(x * 1.2, 1.2)
    n = int(fade_out * SR); x[-n:] *= np.linspace(1, 0, n)[:, None]
    x = x / np.max(np.abs(x)) * 10 ** (target_peak_db / 20)
    return x.astype(np.float32)

def export(slug, x, meta):
    """Save mp3 (+ spectrogram + json meta) into 2026-10-21-pieces/<slug>/."""
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    out = os.path.join(PIECES, slug); os.makedirs(out, exist_ok=True)
    x = master(x)
    tmp = os.path.join(out, slug + ".tmp.wav"); sf.write(tmp, x, SR, subtype="PCM_16")
    mp3 = os.path.join(out, slug + ".mp3")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", tmp, "-codec:a", "libmp3lame", "-b:a", "192k", mp3], check=True)
    os.remove(tmp)
    mono = x.mean(1)
    f, t, S = signal.spectrogram(mono, SR, nperseg=2048, noverlap=1536)
    plt.figure(figsize=(10, 3.2))
    plt.pcolormesh(t, f, 10 * np.log10(S + 1e-12), shading="auto", cmap="magma", vmin=-120, vmax=-30)
    plt.yscale("symlog", linthresh=200); plt.ylim(30, 20000)
    plt.title(meta.get("title", slug).split(" (")[0].encode("ascii", "ignore").decode() or slug); plt.xlabel("s"); plt.ylabel("Hz"); plt.tight_layout()
    plt.savefig(os.path.join(out, "spectrogram.png"), dpi=90); plt.close()
    with open(os.path.join(out, "meta.json"), "w") as fh: json.dump(meta, fh, indent=2, ensure_ascii=False)
    print("exported", mp3, f"{len(x)/SR:.1f}s")
    return mp3
