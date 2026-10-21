"""Piece 4 - "Moon Over Mountain Stream" (月照山河): Chinese pentatonic, guqin/xiao inspired,
with a synthesized Mandarin vocal line.
* Guqin: additive physical-ish model - 14 slightly inharmonic partials with per-partial decay,
  continuous pitch curves for the characteristic slides (吟猱 vibrato / 上下 glissando),
  pluck noise and a body-resonance filter. Harmonic "fanyin" tones as bell-like pure partials.
* Xiao flute: sine + weak 2nd/3rd harmonic + band-passed breath noise, slow attack, vibrato.
* Melody: first-order Markov chain over D gong-mode pentatonic (D E F# A B), phrase-final
  notes forced to D/A, random slides on long notes.
* Vocal: eSpeak-NG Mandarin (cmn) sung via vocal.py on the same pentatonic scale."""
import numpy as np
from common import *
from vocal import sing

r = np.random.default_rng(88)
PENTA = [50, 52, 54, 57, 59, 62, 64, 66, 69, 71, 74]   # D3..D5 gong mode
B = 60 / 66
N = int(90 * SR)

def qin(freq_curve, dur, amp=1.0):
    n = int(dur * SR); t = np.arange(n) / SR
    f = np.broadcast_to(freq_curve, (n,)) if np.ndim(freq_curve) == 0 else freq_curve[:n]
    ph = np.cumsum(f) / SR; x = np.zeros(n)
    for k in range(1, 15):
        inh = np.sqrt(1 + 0.00015 * k * k)
        x += (1 / k ** 1.1) * np.exp(-t * (0.6 + 0.55 * k)) * np.sin(2 * np.pi * k * inh * ph + r.random())
    x += 0.15 * bandpass(noise(n), 1500, 6000) * np.exp(-t * 60)          # finger/nail pluck
    x = 0.7 * x + 0.3 * bandpass(x, 150, 900)                               # wooden body
    return amp * x * np.minimum(1, t / 0.003)

def slide_curve(m0, m1, dur, at=0.45, yin=False):
    n = int(dur * SR); t = np.arange(n) / SR
    mm = m0 + (m1 - m0) * 0.5 * (1 + np.tanh((t - at * dur) / 0.06))
    if yin: mm = mm + 0.25 * np.sin(2 * np.pi * 4.0 * t) * np.exp(-t * 1.2)
    return mtof(mm)

def fanyin(m, dur):
    n = int(dur * SR); t = np.arange(n) / SR
    return 0.5 * np.sin(2 * np.pi * mtof(m) * t) * np.exp(-t * 2.2) + 0.1 * np.sin(4 * np.pi * mtof(m) * t) * np.exp(-t * 4)

def xiao(m, dur):
    n = int(dur * SR); t = np.arange(n) / SR
    f = mtof(m) * (1 + 0.007 * np.sin(2 * np.pi * 5 * t) * np.clip(t / 0.6 - 0.3, 0, 1))
    ph = np.cumsum(f) / SR
    tone = np.sin(2 * np.pi * ph) + 0.12 * np.sin(4 * np.pi * ph) + 0.05 * np.sin(6 * np.pi * ph)
    breath = bandpass(noise(n), mtof(m) * 0.8, min(mtof(m) * 4, 15000)) * 0.25
    return (tone + breath) * adsr(n, 0.18, 0.2, 0.85, 0.35)

# Markov transition: prefer steps of 1-2 positions in the pentatonic ladder
P = np.array([[{0: .3, 1: 3, 2: 2, 3: .6}.get(abs(i - j), .05) for j in range(len(PENTA))] for i in range(len(PENTA))])
P /= P.sum(1, keepdims=True)
qbuf = np.zeros(N); xbuf = np.zeros(N)
t = 0.5; s = 5
# Section A (0-20s): solo qin, free rhythm phrases
def phrase(t, length, lo=0, end_on=(5, 8)):
    global s
    for k in range(length):
        s = int(r.choice(len(PENTA), p=P[s]))
        if k == length - 1: s = min(end_on, key=lambda e: abs(e - s))
        d = float(r.choice([0.5, 1, 1, 1.5, 2]) * B) if k < length - 1 else 3 * B
        m = PENTA[s]
        if d >= 1.5 * B and r.random() < 0.6:
            tgt = PENTA[max(0, min(len(PENTA) - 1, s + int(r.choice([-1, 1]))))]
            fc = slide_curve(m, tgt, d + 1.5, at=0.5 * d / (d + 1.5), yin=r.random() < .5)
        else:
            fc = slide_curve(m, m, d + 1.5, yin=d > B)
        place(qbuf, qin(fc, d + 1.5, 0.6), t); t += d
    return t
t = phrase(t, 7); t = phrase(t + B, 6)
for m in [74, 69, 62]: place(qbuf, fanyin(m + 12, 3), t); t += B
t += B
# Section B: vocal + qin accompaniment + xiao answer
lyr = [("月", 62), ("光", 64), ("照", 69), ("山", 66), ("河", 64),
       ("流", 62), ("水", 59), ("向", 62), ("远", 64), ("方", 62)]
durs = [1, 1, 2, 1, 3, 1, 1, 1, 2, 3]
ev = []; tv = t
for (syl, m), d in zip(lyr, durs):
    ev.append((syl, m + 0, tv, d * B * 0.95)); tv += d * B
    if d >= 2: place(qbuf, qin(slide_curve(m - 12, m - 12, 2.5), 2.5, 0.4), tv - d * B)
vocal_start = t
t = tv + B
# xiao answers the vocal phrase, qin plays the drone of open strings
for m, d in [(74, 2), (71, 1), (69, 1), (66, 2), (64, 1), (62, 3)]:
    place(xbuf, 0.35 * xiao(m, d * B + 0.3), t); t += d * B
for k in range(int((t - vocal_start) / (2 * B))):
    place(qbuf, qin(slide_curve(38, 38, 3), 3, 0.25), vocal_start + k * 2 * B)
# Section C: vocal repeats with xiao heterophony, qin ends with harmonics
ev2 = []; tv = t
for (syl, m), d in zip(lyr, durs):
    ev2.append((syl, m, tv, d * B * 0.95)); place(xbuf, 0.18 * xiao(m + 12, d * B * 0.95), tv); tv += d * B
t = phrase(tv, 5, end_on=(0, 5))
for m in [62, 69, 74]: place(qbuf, fanyin(m + 12, 4), t); t += 1.3 * B
print(f"content ends at {t:.1f}s"); end = int(min(N, (t + 4) * SR))
vox = sing(ev + ev2, N, voice="cmn+f2", speed=110, vib_depth=0.5, vib_rate=5.5)
mix = (reverb(pan(qbuf, -0.15), 3.5, 0.3) + reverb(pan(xbuf, 0.3), 4.0, 0.4) +
       reverb(pan(highpass(vox, 140) * 0.35, 0.05), 3.0, 0.35))
export("2026-10-21-p4-guqin-vocal-moon-over-stream", mix[:end], dict(
    title="Moon Over Mountain Stream (月照山河)", style="Chinese pentatonic, guqin & xiao inspired, Mandarin synthesized vocal",
    key="D gong-mode pentatonic", lyrics="月光照山河，流水向远方",
    method="Additive guqin model with pitch-slide curves + noise-excited xiao (numpy DSP); Markov pentatonic melody; eSpeak-NG cmn singing"))
