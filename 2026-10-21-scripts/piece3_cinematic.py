"""Piece 3 - "Last Light Over the Ridge": orchestral / cinematic trailer cue.
Harmony from music21 Roman numerals (D minor: i-VI-III-VII / i-VI-iv-V), voice-led SATB-style
string voicings, rule-based horn theme, string ostinato, timpani and choir; arranged as a
3-act build (low strings -> horn theme -> tutti). Rendered with FluidSynth GM orchestra patches."""
import numpy as np, pretty_midi as pm
from music21 import roman
from common import *

BPM = 72; B = 60 / BPM; BAR = 4 * B; OFF = 0.8
NUM = ["i", "VI", "III", "VII", "i", "VI", "iv", "V"]
chords = [[p.midi for p in roman.RomanNumeral(n, "d").pitches] for n in NUM]
r = np.random.default_rng(3)

def voice(prev, pcs, lo=50, hi=74):
    """Greedy voice leading: choose 4 notes (pcs, doubled root) in range minimising motion."""
    cands = sorted({m for m in range(lo, hi + 1) if m % 12 in {p % 12 for p in pcs}})
    out = []
    for v in prev:
        best = min((c for c in cands if c not in out), key=lambda c: abs(c - v)); out.append(best)
    return sorted(out)

song = pm.PrettyMIDI(initial_tempo=BPM)
I = lambda prog, name: pm.Instrument(prog, name=name)
strings, cb, horns, timp, choir, ost, brass = I(48, "Strings"), I(43, "Contrabass"), I(60, "Horns"), I(47, "Timpani"), I(52, "Choir"), I(45, "Pizz"), I(61, "Brass")
v = [50, 57, 62, 65]
BARS = 16
for bar in range(BARS):
    t0 = OFF + bar * BAR; ch = chords[bar % 8]; root = ch[0] % 12
    act = 0 if bar < 4 else (1 if bar < 10 else 2)
    v = voice(v, ch)
    vel = [55, 75, 100][act] + bar
    for m in v: strings.notes.append(pm.Note(min(vel, 120), m, t0, t0 + BAR))
    cb.notes.append(pm.Note(min(vel + 10, 125), 36 + root, t0, t0 + BAR))
    # timpani: soft roll at bar starts in act 0, pulse in act 2
    tn = 38 if root in (2, 10, 3) else 45
    if act == 0 and bar % 2 == 1:
        for k in range(16): timp.notes.append(pm.Note(30 + 4 * k, tn, t0 + 3 * B + k * B / 16, t0 + 3 * B + (k + 1) * B / 16))
    if act == 2:
        for bt in [0, 1.5, 2, 3, 3.5]: timp.notes.append(pm.Note(110 if bt == 0 else 85, tn, t0 + bt * B, t0 + bt * B + .3))
    if act >= 1:  # pizz/spiccato 8th ostinato on chord tones
        pat = [0, 2, 1, 2, 0, 2, 1, 3]
        tones = sorted(set([c + 12 for c in ch[:3]] + [ch[0] + 24]))
        for e in range(8):
            ost.notes.append(pm.Note(70 + 15 * (act == 2), tones[pat[e] % len(tones)], t0 + e * B / 2, t0 + e * B / 2 + .2))
    if act == 2:
        for m in v[1:]: choir.notes.append(pm.Note(85, m + 12, t0, t0 + BAR))
        brass.notes.append(pm.Note(95, ch[0] - 12, t0, t0 + 2 * B)); brass.notes.append(pm.Note(95, ch[0] - 5, t0, t0 + 2 * B))
# Horn theme: rule-based, built on chord tones with stepwise passing tones (bars 4-15)
theme = [(0, 2, 0), (2, 1, 1), (3, 1, 2),  (0, 3, 1), (3, 1, 0),  (0, 2, 2), (2, 2, 1), (0, 4, 0)]  # (beat, len, chord-tone idx)
for bar in range(4, BARS):
    ch = chords[bar % 8]; t0 = OFF + bar * BAR
    seg = theme[(bar % 4) * 2:(bar % 4) * 2 + 2]
    for bt, ln, ti in seg:
        m = sorted(ch)[ti] + 12
        if m < 60: m += 12
        horns.notes.append(pm.Note(90 if bar < 10 else 115, m, t0 + bt * B, t0 + (bt + ln) * B))
        if bar >= 10: horns.notes.append(pm.Note(105, m - 12, t0 + bt * B, t0 + (bt + ln) * B))
# final chord
tf = OFF + BARS * BAR
for inst, ms in [(strings, [38, 50, 57, 62, 65, 69]), (choir, [62, 65, 69, 74]), (horns, [62, 69]), (cb, [26])]:
    for m in ms: inst.notes.append(pm.Note(110, m, tf, tf + 4.5))
for k in range(24): timp.notes.append(pm.Note(min(127, 60 + 3 * k), 38, tf + k * B / 8, tf + (k + 1) * B / 8))

def solo(inst):
    s = pm.PrettyMIDI(initial_tempo=BPM); s.instruments.append(inst); return render_midi(s, 0.6)
parts = {i.name: solo(i) for i in (strings, cb, horns, timp, choir, ost, brass)}
n = max(len(x) for x in parts.values()); parts = {k: np.pad(x, ((0, n - len(x)), (0, 0))) for k, x in parts.items()}
g = dict(Strings=1.0, Contrabass=0.9, Horns=0.9, Timpani=1.0, Choir=0.7, Pizz=0.6, Brass=0.7)
dry = sum(g[k] * x for k, x in parts.items())
mix = reverb(dry, 3.2, 0.38, 0.03, 5000)
export("2026-10-21-p3-cinematic-last-light", mix[: int((tf + 7) * SR)], dict(
    title="Last Light Over the Ridge", style="Orchestral / cinematic trailer", bpm=BPM, key="D minor",
    method="music21 Roman-numeral harmony + greedy voice leading + rule-based theme -> pretty_midi -> FluidSynth GM orchestra -> convolution hall reverb"))
