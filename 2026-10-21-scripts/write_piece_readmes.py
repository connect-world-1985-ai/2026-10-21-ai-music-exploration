"""Write a short README.md in every piece folder from meta.json + qa_report.json + notes below."""
import json, os, glob
from common import PIECES
NOTES = {
 "p1": ("Everything is computed sample-by-sample in numpy: anti-aliased PolyBLEP saw/square oscillators, a 7-voice detuned supersaw pad through a time-varying state-variable low-pass (filter opens over the intro), octave-bouncing 8th-note bass, a 16th-note square arpeggio with ping-pong delay, and a 2-operator FM lead with delayed vibrato. Kick = pitch-swept sine, snare = band-passed noise + 190 Hz tone, hats = high-passed noise. Kick-triggered sidechain gain ducks pad/bass/arp.",
        "Synthwave is literally built from these 1980s subtractive/FM synth primitives, so pure DSP is the most honest and controllable technique - no samples needed."),
 "p2": ("pretty_midi builds the arrangement: Dm9-G13-Cmaj9-A7b9 voicings, rolled chords, 58% swung 16th-note boom-bap with random ghost notes, Gaussian timing/velocity humanisation, and a first-order Markov melody over the C major scale (step-weighted transitions, chord-tone snapping on downbeats). Stems are rendered separately with FluidSynth (FluidR3 GM: EP1, fingered bass, vibraphone, GM drums), then a numpy lo-fi chain adds tape wow (0.5 Hz) + flutter (6 Hz) via modulated delay, tanh saturation, 4.2 kHz low-pass, vinyl crackle and hiss.",
        "Lo-fi is about jazz harmony + 'imperfect' texture; GM soundfonts sound cheap dry, but the lo-fi chain turns that cheapness into the aesthetic."),
 "p3": ("Harmony comes from music21 Roman numerals in D minor (i-VI-III-VII | i-VI-iv-V); a greedy voice-leading function picks the closest 4-voice string voicing for each chord. A rule-based horn theme uses chord tones; spiccato/pizz 8th-note ostinato enters in act 2; act 3 adds choir, brass and timpani hits; ends on a tutti Dm chord with a timpani crescendo roll. Seven FluidSynth stems summed into a 3.2 s convolution hall reverb.",
        "Orchestral writing is a symbolic-music problem (harmony, voice leading, orchestration), so a music-theory library + soundfont is the right tool; DSP synthesis of strings would be far worse."),
 "p4": ("Guqin is an additive physical-ish model: 14 slightly inharmonic partials with frequency-dependent decay, driven by continuous pitch curves so notes can slide (上/下 glissando) and waver (吟猱 vibrato), plus nail-noise and a body band-pass. Harmonic 'fanyin' tones are bell-like sines. The xiao flute is sine + weak harmonics + band-passed breath noise with delayed vibrato. Melodies are a Markov chain over the D gong-mode pentatonic scale with phrase endings forced to D/A. The Mandarin line 月光照山河，流水向远方 is sung by eSpeak-NG (cmn, female) through vocal.py, repeated with xiao heterophony an octave up.",
        "Guqin's identity is in pitch slides after the pluck, which soundfonts can't do; an additive model with an explicit pitch curve can. Mandarin vocal tests the singing pipeline on a tonal language."),
 "p5": ("Piano arpeggios, strings, bass and side-stick drums are pretty_midi -> FluidSynth over I-V-vi-IV. The vocal is 'sung' by eSpeak-NG: each syllable is synthesized with SSML prosody range='x-low' (flattens speech intonation), its median f0 is measured with pYIN, it's pitch-shifted to the melody note, and only the voiced nucleus is time-stretched to the note length (consonants keep their natural length). Vibrato is a modulated fractional delay. Verse 2 adds a diatonic third-above harmony and a double with different eSpeak voice variants, panned, with delay + reverb.",
        "No open singing-voice model (DiffSinger, NNSVS, etc.) is installed or small enough; this is the best fully-local, CPU-only, sub-1-MB technique to get recognisable sung words."),
 "p6": ("facebook/musicgen-small (Meta, 300M-param autoregressive transformer over EnCodec 32 kHz tokens, T5 text encoder) run via Hugging Face transformers on CPU (8 cores, no GPU). Prompt: 'late night smooth jazz trio, warm upright bass walking line, brushed drums, mellow grand piano chords and melody, intimate club recording, 90 bpm'; seed 2026, classifier-free guidance 3.0, sampling. Output resampled to 44.1 kHz, pseudo-stereo widened, light room, mastered.",
        "The control experiment: how does an actual generative AI model compare with hand-built agent code? It needs no music theory, only a prompt."),
}
qa = {os.path.basename(os.path.dirname(r["file"])): r for r in json.load(open(os.path.join(PIECES, "qa_report.json")))}
for d in sorted(glob.glob(os.path.join(PIECES, "2026-10-21-p*"))):
    slug = os.path.basename(d); key = slug.split("-")[3]; m = json.load(open(os.path.join(d, "meta.json")))
    how, why = NOTES[key]; q = qa.get(slug, {})
    txt = f"""# {m['title']}

* **Style:** {m['style']}
* **File:** `{slug}.mp3` ({q.get('duration_s','?')} s, peak {q.get('peak_dbfs','?')} dBFS, RMS {q.get('rms_dbfs','?')} dBFS, {q.get('size_mb','?')} MB)
* **Method (short):** {m['method']}
* **Script:** see `2026-10-21-scripts/` (`piece{key[1]}_*.py`)

## How it was made
{how}

## Why this technique
{why}

![spectrogram](spectrogram.png)
"""
    if "lyrics" in m: txt += f"\n**Lyrics:** {m['lyrics'] if isinstance(m['lyrics'], str) else ' / '.join(m['lyrics'])}\n"
    if "prompt" in m: txt += f"\n**Prompt:** {m['prompt']}\n"
    open(os.path.join(d, "README.md"), "w").write(txt)
print("ok")
