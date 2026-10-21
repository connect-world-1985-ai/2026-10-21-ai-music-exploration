"""Piece 5 - "Morning Light": pop ballad with a synthesized lead vocal (English).
Accompaniment: pretty_midi (I-V-vi-IV piano arpeggios, strings, bass, soft drums) -> FluidSynth.
Vocal: eSpeak-NG female voice sung via vocal.py (flattened prosody, pYIN + pitch-shift to melody,
nucleus-only time-stretch, vibrato); second verse adds a diatonic third-above harmony + double."""
import numpy as np, pretty_midi as pm
from common import *
from vocal import sing

BPM = 84; B = 60 / BPM; BAR = 4 * B; OFF = 0.5
CH = {"C": [48, 55, 60, 64], "G": [43, 55, 59, 62], "Am": [45, 57, 60, 64], "F": [41, 53, 57, 60]}
VERSE_CH = ["C", "G", "Am", "F", "C", "G", "F", "G", "C"]
RH = [1, 1, 1, .5, .5, 1, 3]
LINES = [
    (["close", "your", "eyes", "the", "cit", "tee", "sleeps"], [64, 62, 60, 62, 64, 67, 67]),
    (["stars", "are", "fal", "ling", "in", "the", "sea"], [69, 67, 64, 67, 69, 72, 69]),
    (["hold", "my", "hand", "and", "sing", "with", "me"], [64, 64, 67, 69, 67, 64, 62]),
    (["we", "will", "find", "the", "morn", "ing", "light"], [60, 62, 65, 64, 65, 64, 60]),
]
SCALE = [0, 2, 4, 5, 7, 9, 11]
def third_up(m):
    pc = m % 12; i = SCALE.index(pc); j = i + 2
    return m - pc + SCALE[j % 7] + 12 * (j // 7)

form = ["C", "G"] + VERSE_CH + ["F"] + VERSE_CH + ["C"]
v1_start, v2_start = 2, 2 + 9 + 1
song = pm.PrettyMIDI(initial_tempo=BPM)
pno, strg, bass, dr = pm.Instrument(0, name="Piano"), pm.Instrument(49, name="Strings"), pm.Instrument(32, name="Bass"), pm.Instrument(0, is_drum=True, name="Drums")
r = np.random.default_rng(11)
for bar, c in enumerate(form):
    t0 = OFF + bar * BAR; notes = CH[c]
    arp = [notes[0], notes[1], notes[2], notes[3], notes[2] + 12, notes[3], notes[2], notes[1]]
    for e, m in enumerate(arp):
        pno.notes.append(pm.Note(int(r.integers(50, 68)), m, t0 + e * B / 2 + r.normal(0, .006), t0 + e * B / 2 + 1.2 * B))
    if bar >= v1_start:
        bass.notes.append(pm.Note(85, notes[0] - 12 if notes[0] > 40 else notes[0], t0, t0 + BAR * .95))
    if bar >= v2_start - 1:
        for m in notes[1:]: strg.notes.append(pm.Note(60, m + 12, t0, t0 + BAR))
    if v2_start <= bar < len(form) - 1:
        for bt in range(4):
            dr.notes.append(pm.Note(70 if bt % 2 == 0 else 30, 36, t0 + bt * B, t0 + bt * B + .1))
            if bt % 2: dr.notes.append(pm.Note(55, 37, t0 + bt * B, t0 + bt * B + .1))  # side-stick
            for e in range(2): dr.notes.append(pm.Note(int(r.integers(25, 45)), 42, t0 + (bt + e / 2) * B, t0 + (bt + e / 2) * B + .05))
for i in (pno, strg, bass, dr): song.instruments.append(i)
def solo(inst):
    s = pm.PrettyMIDI(initial_tempo=BPM); s.instruments.append(inst); return render_midi(s, 0.6)
parts = [solo(i) for i in (pno, strg, bass, dr)]
total = int((OFF + len(form) * BAR + 4) * SR)
parts = [np.pad(p, ((0, max(0, total - len(p))), (0, 0)))[:total] for p in parts]
acc = 0.9 * parts[0] + 0.5 * parts[1] + 0.8 * parts[2] + 0.6 * parts[3]

def events(start_bar, transform=lambda m: m):
    ev = []; t = OFF + start_bar * BAR
    for li, (syl, mel) in enumerate(LINES):
        rh = RH[:-1] + [RH[-1] + (4 if li == 3 else 0)]
        for s, m, d in zip(syl, mel, rh):
            ev.append((s, transform(m), t, d * B * 0.97)); t += d * B
    return ev
lead = sing(events(v1_start) + events(v2_start), total, voice="en-us+f3", speed=125)
harm = sing(events(v2_start, third_up), total, voice="en-us+f4", speed=125, vib_rate=5.0)
dbl = sing(events(v2_start), total, voice="en-us+f2", speed=125, vib_rate=4.7)
voc = highpass(lead, 120) * 0.55 + 0.0
vox = (pan(voc, 0) + pan(highpass(harm, 150) * 0.22, -0.45) + pan(highpass(dbl, 150) * 0.2, 0.45))
vox = reverb(delay(vox, B * 0.5, 0.25, 0.12), 2.4, 0.3)
mix = acc / np.max(np.abs(acc)) * 0.6 + vox / np.max(np.abs(vox)) * 0.75
mix = reverb(mix, 1.5, 0.12)
export("2026-10-21-p5-ballad-vocal-morning-light", mix, dict(
    title="Morning Light", style="Pop ballad with synthesized English lead vocal + harmony",
    bpm=BPM, key="C major (I-V-vi-IV)", lyrics=[" ".join(l[0]) for l in LINES],
    method="pretty_midi accompaniment -> FluidSynth; eSpeak-NG -> pYIN/pitch-shift/time-stretch 'singing' vocals"))
