"""Synthesised weapon sounds (no samples, fully generated). Called by build_pack.py.
Each sound -> assets/starkffa/sounds/<path>.ogg (mono, 44.1 kHz, vorbis)."""
import numpy as np, subprocess, os, tempfile
from scipy.signal import butter, sosfilt
from scipy.io import wavfile

SR = 44100
rng = np.random.default_rng(42)

def t(sec): return np.arange(int(SR * sec)) / SR
def env(n, attack=0.002, decay=0.1):
    x = np.arange(n) / SR
    a = np.clip(x / attack, 0, 1)
    return a * np.exp(-x / decay)
def sweep(f0, f1, sec, shape=1.0):
    x = t(sec); f = f0 + (f1 - f0) * (x / sec) ** shape
    return np.sin(2 * np.pi * np.cumsum(f) / SR)
def band(sig, lo, hi, order=2):
    sos = butter(order, [lo, hi], btype="band", fs=SR, output="sos"); return sosfilt(sos, sig)
def low(sig, f): return sosfilt(butter(2, f, btype="low", fs=SR, output="sos"), sig)
def high(sig, f): return sosfilt(butter(2, f, btype="high", fs=SR, output="sos"), sig)
def noise(sec): return rng.standard_normal(int(SR * sec))
def mix(*parts):
    n = max(len(p) for p in parts); out = np.zeros(n)
    for p in parts: out[:len(p)] += p
    return out
def at(sig, sec, total):
    out = np.zeros(int(SR * total)); i = int(SR * sec); out[i:i + len(sig)] += sig[:len(out) - i]; return out
def norm(x, peak=0.9):
    m = np.max(np.abs(x)) or 1; return x / m * peak

def fire():        # pneumatic "pfoomp" + spring
    n = 0.35
    thump = sweep(140, 55, 0.12) * env(int(SR * .12), .001, .045)
    air = band(noise(.2), 300, 2500) * env(int(SR * .2), .002, .05)
    spring = sweep(950, 720, .22) * env(int(SR * .22), .004, .07) * .25
    return norm(mix(thump * 1.0, air * .55, at(spring, .02, n)))

def stick():       # wet suction "thwop"
    n = 0.3
    pop = sweep(260, 85, .09, .6) * env(int(SR * .09), .001, .035)
    click = high(noise(.02), 2500) * env(int(SR * .02), .0005, .004) * .5
    squelch = low(noise(.12) * (0.5 + 0.5 * np.sin(2 * np.pi * 38 * t(.12))), 900) * env(int(SR * .12), .01, .04) * .6
    return norm(mix(pop, click, at(squelch, .035, n)))

def reel():        # ratchet zip, ~0.5 s, played while pulling
    n = .5; out = np.zeros(int(SR * n))
    k = 0; s = 0.0
    while s < n - .01:
        c = band(noise(.006), 2500, 6500) * env(int(SR * .006), .0003, .0015) * (0.6 + 0.4 * (s / n))
        out += at(c, s, n); k += 1; s += 0.034 - 0.012 * (s / n)
    whoosh = band(noise(n), 400, 1800) * np.linspace(.05, .35, int(SR * n)) * env(int(SR * n), .05, .9)
    return norm(out + whoosh, .8)

def release():     # cork pop + air
    n = .25
    pop = sweep(700, 280, .03) * env(int(SR * .03), .0005, .01)
    puff = band(noise(.15), 800, 4000) * env(int(SR * .15), .003, .04) * .4
    return norm(mix(pop, at(puff, .005, n)))

def yank():        # elastic twang rising
    n = .4; x = t(.3)
    vib = 1 + .03 * np.sin(2 * np.pi * 22 * x)
    f = (170 + 200 * (x / .3) ** 1.5) * vib
    tw = np.sin(2 * np.pi * np.cumsum(f) / SR) * env(len(x), .003, .12)
    tw += .3 * np.sin(2 * 2 * np.pi * np.cumsum(f) / SR) * env(len(x), .003, .08)
    whoosh = band(noise(.3), 500, 2500) * env(int(SR * .3), .02, .1) * .35
    return norm(mix(tw, whoosh))

SOUNDS = {"grappler/fire": fire, "grappler/stick": stick, "grappler/reel": reel,
          "grappler/release": release, "grappler/yank": yank}

def build(assets_dir, ns):
    defs = {}
    for path, fn in SOUNDS.items():
        x = fn()
        x = np.concatenate([x, np.zeros(int(SR * .02))])
        out = os.path.join(assets_dir, ns, "sounds", path + ".ogg"); os.makedirs(os.path.dirname(out), exist_ok=True)
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f: wav = f.name
        wavfile.write(wav, SR, (x * 32767).astype(np.int16))
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", wav, "-c:a", "libvorbis", "-q:a", "5", "-ac", "1", out], check=True)
        os.remove(wav)
        key = path.replace("/", ".")
        defs[key] = {"subtitle": f"subtitles.{ns}.{key}", "sounds": [{"name": f"{ns}:{path}"}]}
    return defs
