"""Piece 2 - "Rainy Desk": lo-fi hip hop. Algorithmic composition with pretty_midi
(extended jazz chords ii-V-I-VI, swung 16ths, humanised timing/velocity, first-order Markov
melody over chord tones) rendered through FluidSynth + FluidR3 GM soundfont, then numpy
"lo-fi" processing: tape wow/flutter, low-pass, saturation, vinyl crackle and hiss."""
import numpy as np, pretty_midi as pm
from common import *

BPM = 76; B = 60 / BPM; BAR = 4 * B; BARS = 16; OFF = 1.0
CHORDS = [[50, 53, 57, 60, 64], [43, 53, 57, 59, 64], [48, 52, 55, 59, 62], [45, 52, 55, 58, 61]]  # Dm9 G13 Cmaj9 A7b9
SCALE = [62, 64, 65, 67, 69, 71, 72, 74, 76, 77, 79]
r = np.random.default_rng(7)
def hum(t, amt=0.012): return max(0, t + r.normal(0, amt))
def swing(step):  # 16th-note swing ~58%
    pair, odd = divmod(step, 2); return pair * B / 2 + (0.58 if odd else 0) * B / 2

song = pm.PrettyMIDI(initial_tempo=BPM)
ep = pm.Instrument(4, name="EP"); bass = pm.Instrument(33, name="Bass"); vib = pm.Instrument(11, name="Vibes")
dr = pm.Instrument(0, is_drum=True, name="Drums")
for bar in range(BARS):
    t0 = OFF + bar * BAR; ch = CHORDS[bar % 4]
    # EP: chord on 1 (rolled), re-voiced stab on the "and" of 2
    for i, n in enumerate(ch[1:]):
        ep.notes.append(pm.Note(int(r.integers(55, 72)), n, hum(t0 + i * 0.018), t0 + 2.3 * B))
    if bar % 2: 
        for n in ch[2:]:
            ep.notes.append(pm.Note(int(r.integers(45, 60)), n + 12, hum(t0 + 2.5 * B), t0 + 3.8 * B))
    # bass: root, fifth, approach note
    root = ch[0] - 12 if ch[0] > 45 else ch[0]
    nxt = CHORDS[(bar + 1) % 4][0]; nxt = nxt - 12 if nxt > 45 else nxt
    for bt, n, d in [(0, root, 1.4), (1.5, root + 7, 0.9), (3, root + 12, 0.45), (3.5, nxt + 1, 0.45)]:
        bass.notes.append(pm.Note(int(r.integers(80, 100)), n, hum(t0 + bt * B), t0 + (bt + d) * B))
    if bar >= 2:  # boom-bap with swung hats and ghost notes
        for st in range(16):
            ts = t0 + swing(st)
            if st in (0, 10) or (st == 7 and bar % 2): dr.notes.append(pm.Note(int(r.integers(95, 115)), 36, hum(ts, .006), ts + .1))
            if st in (4, 12): dr.notes.append(pm.Note(int(r.integers(85, 100)), 38, hum(ts, .01), ts + .1))
            if st % 2 == 0 or r.random() < .3: dr.notes.append(pm.Note(int(r.integers(30, 65)), 42, hum(ts, .008), ts + .05))
            if st == 15 and r.random() < .4: dr.notes.append(pm.Note(30, 38, hum(ts), ts + .05))
# Markov melody (bars 4-15): states = scale-degree index; transitions favour steps, chord tones on downbeats
P = np.zeros((len(SCALE), len(SCALE)))
for i in range(len(SCALE)):
    for j in range(len(SCALE)):
        P[i, j] = {0: .4, 1: 3, 2: 1.5, 3: .6, 4: .4}.get(abs(i - j), .05)
P /= P.sum(1, keepdims=True)
state = 4
for bar in range(4, BARS):
    t0 = OFF + bar * BAR; ch = CHORDS[bar % 4]; tones = {c % 12 for c in ch}
    rhythm = [[0, 1, 1.5, 2.5], [0, .5, 1.5, 3], [.5, 1, 2, 3.5], [0, 2]][r.integers(4)]
    for k, bt in enumerate(rhythm):
        state = r.choice(len(SCALE), p=P[state])
        if k == 0:  # snap to nearest chord tone
            cands = [i for i, s in enumerate(SCALE) if s % 12 in tones]
            state = min(cands, key=lambda i: abs(i - state))
        dur = (rhythm[k + 1] - bt if k + 1 < len(rhythm) else 4 - bt) * B * 0.9
        vib.notes.append(pm.Note(int(r.integers(60, 85)), SCALE[state], hum(t0 + bt * B), t0 + bt * B + dur))
for i in (ep, bass, vib, dr): song.instruments.append(i)

def solo(inst):
    s = pm.PrettyMIDI(initial_tempo=BPM); s.instruments.append(inst); return render_midi(s, 0.6)
st = {i.name: solo(i) for i in (ep, bass, vib, dr)}
n = max(len(v) for v in st.values()); st = {k: np.pad(v, ((0, n - len(v)), (0, 0))) for k, v in st.items()}
mix = 0.9 * st["EP"] + 1.1 * st["Bass"] + 0.55 * reverb(st["Vibes"], 2.0, 0.35) + 0.8 * st["Drums"]
# --- lo-fi chain ---
t = np.arange(n) / SR
d = (0.0018 * np.sin(2 * np.pi * 0.5 * t) + 0.0003 * np.sin(2 * np.pi * 6.0 * t)) * SR + 100  # wow + flutter (samples)
idx = np.clip(np.arange(n) - d, 0, n - 1)
mix = np.stack([np.interp(idx, np.arange(n), mix[:, c]) for c in range(2)], 1)
mix = lowpass(softclip(mix * 1.5, 1.8), 4200, 2); mix = highpass(mix, 60)
crackle = np.zeros(n); pops = r.integers(0, n, int(n / SR * 9)); crackle[pops] = r.normal(0, 0.5, len(pops))
crackle = bandpass(crackle, 800, 6000) + 0.004 * lowpass(noise(n), 3000)
mix = mix / np.max(np.abs(mix)) + 0.25 * pan(crackle, 0)
export("2026-10-21-p2-lofi-rainy-desk", mix[: int((OFF + BARS * BAR + 2) * SR)], dict(
    title="Rainy Desk", style="Lo-fi hip hop / jazzy chillhop", bpm=BPM, key="C major (ii-V-I-VI)",
    method="pretty_midi algorithmic composition (swing, humanisation, Markov melody) -> FluidSynth FluidR3 GM -> numpy lo-fi chain"))
