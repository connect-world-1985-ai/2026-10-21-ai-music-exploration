"""Piece 1 - "Neon Overdrive": synthwave, 100% numpy/scipy DSP (no samples, no soundfonts).
Supersaw pad, PolyBLEP saw bass, square arpeggio with ping-pong delay, FM lead,
kick/snare/hat synthesised from sine sweeps and filtered noise, sidechain ducking, gated reverb."""
import numpy as np
from common import *

BPM = 104; B = 60 / BPM; BAR = 4 * B
PROG = [(57, [57, 60, 64]), (53, [53, 57, 60]), (48, [55, 60, 64]), (55, [55, 59, 62])]  # Am F C G
BARS = 24
N = int((BARS * BAR + 3) * SR)
L = lambda: np.zeros(N)

def kick():
    n = int(0.45 * SR); t = np.arange(n) / SR
    f = 45 + 120 * np.exp(-t * 28)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 7) + 0.3 * noise(n) * np.exp(-t * 200)
def snare():
    n = int(0.3 * SR); t = np.arange(n) / SR
    return 0.6 * bandpass(noise(n), 1200, 8000) * np.exp(-t * 18) + 0.5 * np.sin(2 * np.pi * 190 * t) * np.exp(-t * 25)
def hat(open_=False):
    n = int((0.25 if open_ else 0.05) * SR); t = np.arange(n) / SR
    return highpass(noise(n), 7000, 4) * np.exp(-t * (12 if open_ else 80))

drums, snares, bass, pad, arp, lead = L(), L(), L(), L(), L(), L()
side = np.ones(N)
k = kick(); s = snare(); h = hat(); ho = hat(True)
for bar in range(BARS):
    t0 = 1.5 + bar * BAR
    root, chord = PROG[bar % 4]
    intro = bar < 4; outro = bar >= 22
    if not intro:
        for beat in range(4):
            place(drums, k, t0 + beat * B)
            i = int((t0 + beat * B) * SR); m = int(0.35 * SR)
            side[i:i + m] = np.minimum(side[i:i + m], 1 - 0.7 * np.exp(-np.arange(m) / SR * 9))
            if beat in (1, 3): place(snares, s, t0 + beat * B)
            for e in range(2):
                place(drums, 0.35 * (ho if (e == 1 and beat == 3) else h), t0 + beat * B + e * B / 2)
    # bass: driving 8ths, octave jumps
    if bar >= 2:
        for e in range(8):
            m = root - 24 + (12 if e % 2 else 0); n = int(B / 2 * SR * 0.9)
            x = saw(mtof(m), n) + 0.5 * square(mtof(m - 12), n)
            x = lowpass(x, 900) * adsr(n, 0.003, 0.08, 0.6, 0.03)
            place(bass, 0.45 * x, t0 + e * B / 2)
    # supersaw pad: 7 detuned saws per chord note
    n = int(BAR * SR)
    x = np.zeros(n)
    for m in chord + [chord[0] + 12]:
        for d in np.linspace(-0.18, 0.18, 7):
            x += saw(mtof(m + d), n, rng.random()) / 7
    pad[int(t0 * SR):int(t0 * SR) + n] += 0.18 * x * adsr(n, 0.25, 0.3, 0.8, 0.3)
    # 16th arpeggio (square), enters bar 4
    if bar >= 4 and not outro:
        pat = [0, 1, 2, 3, 2, 1, 0, 2]
        notes = chord + [chord[0] + 12]
        for st in range(16):
            m = notes[pat[st % 8]] + 12; n = int(B / 4 * SR)
            place(arp, 0.12 * square(mtof(m), n, 0.25) * adsr(n, 0.002, 0.05, 0.3, 0.02), t0 + st * B / 4)
# FM lead melody in bars 12-21 (A minor pentatonic hook, two 4-bar phrases + answer)
mel = [(69, 1), (72, 1), (74, 1.5), (72, .5), (76, 2), (74, 1), (72, 1), (69, 3), (67, 1),
       (65, 1), (69, 1), (72, 2), (74, 1.5), (72, .5), (71, 1), (67, 1), (69, 4)]
t = 1.5 + 12 * BAR
for rep in range(2):
    for m, beats in mel:
        dur = beats * B; n = int(dur * SR); tt = np.arange(n) / SR
        f = mtof(m) * (1 + 0.006 * np.sin(2 * np.pi * 5.5 * tt) * np.clip(tt / 0.3, 0, 1))
        mod = 2.2 * np.exp(-tt * 3) + 0.6
        ph = np.cumsum(f) / SR
        x = np.sin(2 * np.pi * ph + mod * np.sin(2 * np.pi * 2 * ph)) + 0.25 * saw(f, n)
        place(lead, 0.22 * lowpass(x, 5000) * adsr(n, 0.02, 0.2, 0.75, 0.08), t)
        t += dur
# filter sweep on pad: opens over the intro
fc = np.interp(np.arange(N) / SR, [0, 1.5 + 4 * BAR, 1.5 + 12 * BAR, N / SR], [300, 2500, 4500, 1200])
pad = sweep_lowpass(pad, fc)
mix = (pan(drums, 0) * 1.0 + reverb(pan(snares, 0), 0.6, 0.35) + pan(bass * side, 0) +
       reverb(np.stack([pad * side, np.roll(pad, 400) * side], 1), 3.0, 0.35) +
       delay(pan(arp, -0.3), B * 0.75, 0.4, 0.35) * side[:, None] +
       reverb(delay(pan(lead, 0.15), B * 0.5, 0.3, 0.25), 2.5, 0.3))
end = int((1.5 + BARS * BAR + 2.5) * SR)
export("2026-10-21-p1-synthwave-neon-overdrive", mix[:end], dict(
    title="Neon Overdrive", style="Synthwave / retro EDM", bpm=BPM, key="A minor",
    method="Pure numpy/scipy DSP synthesis: PolyBLEP saw/square oscillators, supersaw, FM lead, noise drums, sidechain, convolution reverb"))
