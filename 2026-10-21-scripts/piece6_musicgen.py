"""Piece 6: text-to-music with facebook/musicgen-small (Meta, 300M params) on CPU via HF transformers.
Run inside .venv-ai (torch CPU + transformers). Writes a raw wav; mastering is done by finalize step."""
import time, sys, os, torch, numpy as np, soundfile as sf
from transformers import AutoProcessor, MusicgenForConditionalGeneration
OUT = sys.argv[1] if len(sys.argv) > 1 else "musicgen_raw.wav"
PROMPT = ("late night smooth jazz trio, warm upright bass walking line, brushed drums, "
          "mellow grand piano chords and melody, intimate club recording, 90 bpm")
torch.manual_seed(2026)
torch.set_num_threads(os.cpu_count())
t0 = time.time()
proc = AutoProcessor.from_pretrained("facebook/musicgen-small")
model = MusicgenForConditionalGeneration.from_pretrained("facebook/musicgen-small")
print("loaded in", round(time.time()-t0, 1), "s", flush=True)
inputs = proc(text=[PROMPT], padding=True, return_tensors="pt")
t1 = time.time()
# ~50 tokens per second of audio; 1600 tokens ~= 32 s (model trained on 30 s clips)
with torch.inference_mode():
    audio = model.generate(**inputs, do_sample=True, guidance_scale=3.0, max_new_tokens=1600)
sr = model.config.audio_encoder.sampling_rate
y = audio[0, 0].cpu().numpy().astype(np.float32)
sf.write(OUT, y, sr)
print(f"generated {len(y)/sr:.1f}s audio at {sr} Hz in {time.time()-t1:.1f}s", flush=True)
