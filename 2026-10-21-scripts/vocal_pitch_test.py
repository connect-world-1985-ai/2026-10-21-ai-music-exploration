"""Objective check of the eSpeak 'singing' pipeline: sing test syllables at target notes and
measure the pYIN median pitch error (cents) and pitch stability (std, cents) of the result."""
import numpy as np, librosa
from common import SR, mtof
from vocal import sing_note
tests = [("close", 64, "en-us+f3"), ("eyes", 60, "en-us+f3"), ("sea", 69, "en-us+f3"), ("light", 60, "en-us+f3"),
         ("月", 62, "cmn+f2"), ("照", 69, "cmn+f2"), ("河", 64, "cmn+f2"), ("水", 59, "cmn+f2")]
errs = []
for txt, m, v in tests:
    y = sing_note(txt, m, 1.2, voice=v, vib_depth=0.0)
    f0, vf, _ = librosa.pyin(y, fmin=80, fmax=800, sr=SR)
    c = 1200 * np.log2(f0[vf] / mtof(m))
    errs.append(abs(np.median(c)))
    print(f"{txt:6s} {v:9s} target {m}: median err {np.median(c):+6.1f} c, spread(std) {np.std(c):5.1f} c, voiced {vf.mean():.0%}")
print("mean |median error| =", round(float(np.mean(errs)), 1), "cents")
