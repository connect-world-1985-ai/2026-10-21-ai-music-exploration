# 2026-10-21 AI / Agent Music Exploration

How far can an AI agent get at **music production** on a plain cloud Linux box (8 CPU cores, 15 GB RAM,
**no GPU**, no DAW, no commercial plugins), writing all the code itself? Six ~30–77 s pieces in six
different styles, made with four families of technique:

| # | Title | Style | Technique | Duration | File |
|---|-------|-------|-----------|---------:|------|
| 1 | Neon Overdrive | Synthwave / retro EDM | Pure numpy/scipy DSP synthesis | 58.4 s | [`2026-10-21-pieces/2026-10-21-p1-synthwave-neon-overdrive/…mp3`](2026-10-21-pieces/2026-10-21-p1-synthwave-neon-overdrive/2026-10-21-p1-synthwave-neon-overdrive.mp3) |
| 2 | Rainy Desk | Lo-fi hip hop | Algorithmic MIDI (pretty_midi, Markov melody, swing) → FluidSynth → numpy lo-fi FX | 53.5 s | [`…p2-lofi-rainy-desk.mp3`](2026-10-21-pieces/2026-10-21-p2-lofi-rainy-desk/2026-10-21-p2-lofi-rainy-desk.mp3) |
| 3 | Last Light Over the Ridge | Orchestral / cinematic | music21 Roman-numeral harmony + voice leading → FluidSynth GM orchestra | 61.1 s | [`…p3-cinematic-last-light.mp3`](2026-10-21-pieces/2026-10-21-p3-cinematic-last-light/2026-10-21-p3-cinematic-last-light.mp3) |
| 4 | Moon Over Mountain Stream (月照山河) | Chinese pentatonic, guqin/xiao + **Mandarin vocal** | Additive guqin model with slides, breath-noise xiao, Markov pentatonic melody, eSpeak-NG singing | 76.7 s | [`…p4-guqin-vocal-moon-over-stream.mp3`](2026-10-21-pieces/2026-10-21-p4-guqin-vocal-moon-over-stream/2026-10-21-p4-guqin-vocal-moon-over-stream.mp3) |
| 5 | Morning Light | Pop ballad + **English vocal & harmony** | pretty_midi → FluidSynth accompaniment; eSpeak-NG → pYIN → pitch-shift → nucleus time-stretch → vibrato | 67.4 s | [`…p5-ballad-vocal-morning-light.mp3`](2026-10-21-pieces/2026-10-21-p5-ballad-vocal-morning-light/2026-10-21-p5-ballad-vocal-morning-light.mp3) |
| 6 | Late Night Trio | Smooth jazz piano trio | **AI text-to-music: facebook/musicgen-small** on CPU | 31.9 s | [`…p6-ai-musicgen-late-night-trio.mp3`](2026-10-21-pieces/2026-10-21-p6-ai-musicgen-late-night-trio/2026-10-21-p6-ai-musicgen-late-night-trio.mp3) |

Each piece folder has its own `README.md` (method + why), `meta.json` and `spectrogram.png`.
All files are 192 kbps MP3 (0.8–1.8 MB each, ~9.7 MB total); WAVs were not committed to keep the repo small.

## Environment / tool inventory (as found, then installed)

| Item | Status at start | Action |
|------|-----------------|--------|
| GPU | none (`nvidia-smi` absent) | everything on CPU |
| Python 3.13.5, numpy 2.5 | present | — |
| scipy, soundfile, librosa 1.0, pretty_midi, mido, music21, matplotlib | missing | pip-installed in `.venv` |
| pyworld (WORLD vocoder) | missing | **pip build failed** (C extension compile error) → used librosa pYIN + phase-vocoder pitch shift instead |
| FluidSynth | not present (had been removed) | apt: fluidsynth 2.4.4 |
| SoundFont | no .sf2 anywhere | apt: fluid-soundfont-gm (FluidR3_GM.sf2, 142 MB) |
| ffmpeg | present | used for MP3 encode/decode |
| sox, lame | missing | apt-installed (available, not essential) |
| eSpeak-NG 1.52 | missing | apt; used for English (en-us+f2/f3/f4) and Mandarin (cmn+f2) |
| festival / piper / Coqui TTS / singing engines (DiffSinger, NNSVS, OpenUtau) | absent | not installed (heavy or no CPU-friendly packaged singing model) |
| torch (CPU) + transformers | missing | pip in separate `.venv-ai` (1.3 GB) |
| facebook/musicgen-small | — | downloaded (~2.4 GB HF cache), **worked**: 32 s of audio in 195–404 s CPU time |

## Techniques tried

1. **Pure DSP synthesis** (piece 1, guqin/xiao in piece 4): PolyBLEP oscillators, supersaw, FM, state-variable filter sweeps, noise drums, sidechain, convolution reverb from synthetic IRs, modulated-delay vibrato/wow, additive inharmonic plucked-string model with pitch curves.
2. **Algorithmic composition** (pieces 2–5): Roman-numeral harmony (music21), greedy voice leading, first-order Markov melodies with chord-tone snapping, swing + Gaussian humanisation, rule-based themes, 3-act arrangement logic.
3. **Soundfont rendering** (pieces 2, 3, 5): each instrument rendered as a separate FluidSynth stem so it can be processed and balanced individually.
4. **Synthesized singing** (pieces 4, 5): eSpeak-NG formant TTS → SSML `prosody range="x-low"` to flatten intonation → pYIN f0 → pitch-shift to note → time-stretch only the voiced nucleus → vibrato → harmony/double voices.
5. **Generative AI model** (piece 6): MusicGen-small text-to-music.
6. **QA / "listen proxy"** (`qa_check.py`, `vocal_pitch_test.py`): every MP3 decodes; 30 ≤ duration ≤ 90 s; peak ≤ −0.5 dBFS (all are −1.0 to −1.3 dBFS); RMS −12 to −16 dBFS (not silent); spectrogram rendered. Vocal pitch test: mean absolute median pitch error **3.8 cents** vs target, but within-note pitch spread **~37–44 cents (English)** and **~14–30 cents (Mandarin)**.

**Failed / skipped:** pyworld wouldn't compile (would have allowed proper f0 flattening and formant-preserving shifts); the first MusicGen run gave 29.9 s (just under the 30 s floor) so it was re-run with 1600 tokens (31.9 s, 404 s on CPU). No singing-voice model was attempted: DiffSinger/NNSVS need voicebanks + GPU-oriented stacks, Bark/Suno-style models are several GB and very slow on CPU — outside the time/size budget.

## Honest quality assessment — the ceiling reached

**What is convincing**
* **Synthwave (1)** is the strongest hand-made piece: the genre *is* synthesis, so numpy oscillators + sidechain + delay land close to an amateur bedroom production. Weaknesses: static arrangement, no real mixing automation, FM lead is plain.
* **Lo-fi (2)** works because the genre forgives cheap sounds; jazz voicings + swing + the wow/crackle chain hide General-MIDI thinness. It sounds like a passable background loop, not a release.
* **MusicGen (6)** is the most *realistic-sounding* audio (real-ish piano/bass/brush timbres, natural groove and room) with zero music theory written — but at 32 kHz mono, with EnCodec artefacts (smeared transients, "underwater" highs), no control over form, harmony or exact tempo, and only ~30 s coherence. Slow on CPU (~6–12× slower than real time).

**What is not convincing**
* **Vocals (4, 5)** are the clear weak point: intelligible and on pitch on average, but **robotic** — eSpeak is a 1990s-style formant voice, phase-vocoder stretching makes long vowels buzzy/phasey, there is no breath, no legato between syllables, no dynamics. It reads as "vocoder robot sings", charming at best. Mandarin lexical tones are flattened, which helps pitch accuracy but hurts naturalness.
* **Orchestral (3)** has sound harmony and a real build, but **MIDI stiffness** is obvious: GM strings/horns with fixed samples, no keyswitch articulations, no CC1/CC11 expression curves, quantised attacks; it sounds like a 2005 game soundtrack mock-up.
* **Guqin (4)**: slides are idiomatic and the timbre is "plucked + woody", but it's closer to a koto/harp than a real qin (no string-noise scrapes, no 按音 decay character). Melody is plausible pentatonic noodling, not a composed piece with intent.
* General: Markov/rule melodies are **locally fine but globally aimless**; mixes were never checked by human ears (only metrics + spectrograms).

**Ceiling, in one line:** a single agent on a CPU box can reach *competent demo / game-jam* quality for synthetic genres, *mock-up* quality for acoustic genres, and *robot-novelty* quality for vocals; the generative model gives the most realistic timbre but the least control.

**What would raise the ceiling**
1. A GPU + larger models: MusicGen-medium/large or MusicGen-melody (condition on our own MIDI melody), Stable Audio Open, YuE / ACE-Step / DiffRhythm-style song models for real sung vocals.
2. A real singing synthesizer: DiffSinger / NNSVS / OpenUtau with a voicebank, or RVC voice conversion on top of the current eSpeak guide vocal; pyworld/WORLD for clean f0 replacement.
3. Better instruments: high-quality multi-articulation SFZ/SF2 libraries (e.g. VSCO-2 orchestra, Salamander piano) via sfizz; expression CC automation.
4. Smarter composition: a symbolic music LM (e.g. a MIDI transformer) for melody/phrase structure, plus explicit form (verse/chorus/bridge) and motif development.
5. A real mastering chain (multiband compression, LUFS targeting) and a perceptual-quality metric (e.g. FAD / audiobox-aesthetics) as an automatic "ear".

## Reproduce

```bash
./regenerate.sh            # pieces 1-5 (+ QA)  ~2 min
./regenerate.sh --with-ai  # also piece 6 via MusicGen (CPU, ~4-7 min, ~2.4 GB weights once)
```
Scripts: `2026-10-21-scripts/` — `common.py` (DSP, FluidSynth render, mastering, export), `vocal.py` (singing),
`piece1…piece6*.py`, `qa_check.py`, `vocal_pitch_test.py`, `write_piece_readmes.py`. Requirements: `requirements.txt`, `requirements-ai.txt`.
Random seeds are fixed, so re-runs are deterministic except MusicGen sampling across library versions.

*Made 2026-10-21 by Grok Bot (Mary) for Raymond Shen; all code written locally on the box, no cloud agents.*
