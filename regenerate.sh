#!/usr/bin/env bash
# One-command regeneration of all pieces. Usage: ./regenerate.sh [--with-ai]
set -euo pipefail
cd "$(dirname "$0")"
sudo apt-get install -y fluidsynth fluid-soundfont-gm espeak-ng ffmpeg >/dev/null 2>&1 || echo "(skipping apt; ensure fluidsynth, FluidR3_GM.sf2, espeak-ng, ffmpeg exist)"
[ -d .venv ] || { python3 -m venv .venv && .venv/bin/pip install -q -r requirements.txt; }
S=2026-10-21-scripts
for p in piece1_synthwave piece2_lofi piece3_cinematic piece4_guqin_vocal piece5_ballad_vocal; do
  echo "== $p"; .venv/bin/python "$S/$p.py" 2>&1 | grep -E 'exported|content' || true
done
if [ "${1:-}" = "--with-ai" ]; then
  [ -d .venv-ai ] || { python3 -m venv .venv-ai && .venv-ai/bin/pip install -q torch --index-url https://download.pytorch.org/whl/cpu && .venv-ai/bin/pip install -q transformers scipy soundfile; }
  .venv-ai/bin/python "$S/piece6_musicgen.py" /tmp/musicgen_raw.wav     # ~3-4 min on 8 CPU cores, downloads ~2.4 GB weights once
  .venv/bin/python "$S/piece6_finalize.py" /tmp/musicgen_raw.wav
fi
.venv/bin/python "$S/qa_check.py"
.venv/bin/python "$S/vocal_pitch_test.py" 2>/dev/null | tail -1
