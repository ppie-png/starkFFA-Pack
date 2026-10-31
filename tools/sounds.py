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

def void_launch():  # deep "whum" with a reverse swell
    n = .45; x = t(.4)
    whum = np.sin(2 * np.pi * np.cumsum(70 + 40 * np.exp(-x / .08)) / SR) * env(len(x), .004, .16)
    swell = band(noise(.25), 200, 1200) * np.linspace(0, 1, int(SR * .25)) ** 2 * .5
    zap = sweep(1400, 300, .12, .5) * env(int(SR * .12), .001, .04) * .3
    return norm(mix(at(swell, 0, n), at(whum, .12, n), at(zap, .14, n)))

def void_hum():     # 1.5 s low drone that gets stronger, wobbling
    n = 1.5; x = t(n)
    f = 48 + 10 * x / n
    drone = np.sin(2 * np.pi * np.cumsum(f) / SR) + .5 * np.sin(2 * np.pi * np.cumsum(f * 2.01) / SR)
    wob = .6 + .4 * np.sin(2 * np.pi * (3 + 4 * x / n) * x)
    air = low(noise(n), 500) * .25
    e = np.clip(x / .2, 0, 1) * (0.6 + 0.4 * x / n) * np.clip((n - x) / .08, 0, 1)
    return norm((drone * wob + air) * e, .8)

def void_collapse(): # implosion: reverse suck then boom
    n = .7
    suck = band(noise(.25), 300, 3000) * np.linspace(0, 1, int(SR * .25)) ** 3
    boom = sweep(90, 35, .4, .7) * env(int(SR * .4), .001, .13)
    crack = high(noise(.03), 1500) * env(int(SR * .03), .0005, .008) * .6
    return norm(mix(at(suck, 0, n), at(boom * 1.2, .24, n), at(crack, .24, n)))

def void_rumble():   # 1.5 s sub rumble + rising airy whoosh, layered with void.hum
    n = 1.5; x = t(n)
    sub = np.sin(2 * np.pi * np.cumsum(32 + 6 * np.sin(2 * np.pi * 1.3 * x)) / SR)
    grit = low(noise(n), 160) * 1.2
    rise = band(noise(n), 300, 2400) * (x / n) ** 2.2 * .5
    e = np.clip(x / .25, 0, 1) * np.clip((n - x) / .1, 0, 1)
    return norm((sub * .9 + grit + rise) * e, .85)


# ---------------------------------------------------------------- W4-W9 + UI
def chime(freqs, sec, decay=.25, amp=1.0):
    x = t(sec); out = np.zeros(len(x))
    for i, f in enumerate(freqs): out += np.sin(2 * np.pi * f * x) * np.exp(-x / (decay * (1 - .15 * i))) / (1 + i * .6)
    return out * np.clip(x / .004, 0, 1) * amp

def soul_feast():   # ghostly inhale + bright soul chime
    n = .8
    inhale = band(noise(.45), 500, 3500) * np.linspace(0, 1, int(SR * .45)) ** 2 * .6
    ch = chime([660, 990, 1320, 1760], .6, .3)
    low_ = sweep(180, 260, .5) * env(int(SR * .5), .05, .25) * .4
    return norm(mix(at(inhale, 0, n), at(ch, .38, n), at(low_, .3, n)))

def soul_drain():   # soft "shhk" + tiny chime
    n = .3
    sh = band(noise(.12), 2000, 7000) * env(int(SR * .12), .002, .03) * .7
    ch = chime([1320, 1980], .25, .08) * .5
    return norm(mix(sh, at(ch, .03, n)), .7)

def soul_end():     # fading whisper
    n = .7; x = t(n)
    wh = band(noise(n), 900, 4000) * (0.5 + 0.5 * np.sin(2 * np.pi * 7 * x)) * np.exp(-x / .25) * np.clip(x / .05, 0, 1)
    return norm(wh, .6)

def shadow_smoke(): # pressurised hiss burst
    n = .9; x = t(n)
    hiss = high(noise(n), 1800) * np.exp(-x / .3) * np.clip(x / .01, 0, 1)
    whoomp = sweep(120, 50, .2) * env(int(SR * .2), .002, .07) * .9
    return norm(mix(hiss * .8, whoomp))

def shadow_backstab():  # whisper sting + crit stab
    n = .5
    sting = sweep(2400, 900, .12, .4) * env(int(SR * .12), .001, .04) * .6
    stab = band(noise(.05), 800, 5000) * env(int(SR * .05), .0005, .012)
    tail = band(noise(.3), 1200, 3500) * env(int(SR * .3), .02, .08) * .3
    return norm(mix(stab, at(sting, .01, n), at(tail, .05, n)))

def blink_step():   # glassy "zhip"
    n = .35
    z = sweep(400, 3200, .08, .5) * env(int(SR * .08), .001, .05) * .7
    gl = chime([2093, 3136, 4186], .3, .07) * .6
    air = band(noise(.1), 3000, 9000) * env(int(SR * .1), .001, .03) * .3
    return norm(mix(z, at(gl, .05, n), air))

def blink_shatter():  # glass shatter
    n = .6; out = np.zeros(int(SR * n))
    for i in range(14):
        f = rng.uniform(2500, 7000); s0 = rng.uniform(0, .12)
        out += at(chime([f, f * 1.5], .2, rng.uniform(.03, .08)) * rng.uniform(.3, .8), s0, n)
    crack = high(noise(.04), 2500) * env(int(SR * .04), .0005, .01)
    return norm(mix(out, crack))

def shield_parry():  # deep "bwomm" + metallic ring
    n = 1.0
    bw = sweep(110, 55, .5, .6) * env(int(SR * .5), .002, .18)
    ring = chime([523, 784, 1046, 1568], .9, .35) * .5
    hit = band(noise(.03), 1000, 6000) * env(int(SR * .03), .0005, .008) * .7
    return norm(mix(bw, ring, hit))

def storm_lunge():   # crackle charge + thunder snap
    n = .8; x = t(.35)
    crackle = band(noise(.35), 2000, 8000) * (rng.random(len(x)) > .93) * np.linspace(.3, 1, len(x)) * 1.5
    snap = high(noise(.05), 1500) * env(int(SR * .05), .0003, .015)
    boom = sweep(90, 40, .45, .6) * env(int(SR * .45), .002, .15) * .9
    return norm(mix(at(crackle, 0, n), at(snap, .33, n), at(boom, .34, n)))

def storm_zap():     # short electric zap
    n = .25; x = t(.15)
    buzz = np.sign(np.sin(2 * np.pi * 180 * x)) * env(len(x), .001, .04) * .5
    arc = band(noise(.15), 3000, 9000) * env(len(x), .001, .03)
    return norm(mix(buzz, arc), .8)

def frost_slam():    # crack + deep thud + crystalline shimmer
    n = 1.0
    crack = high(noise(.04), 2000) * env(int(SR * .04), .0003, .01)
    thud = sweep(80, 35, .4, .6) * env(int(SR * .4), .002, .14) * 1.1
    shimmer = chime([1760, 2349, 2794, 3520], .8, .3) * .25
    return norm(mix(crack, thud, at(shimmer, .05, n)))

def frost_shatter():  # ice breaking
    n = .7; out = np.zeros(int(SR * n))
    for i in range(18):
        f = rng.uniform(1500, 5000); s0 = rng.uniform(0, .2)
        out += at(chime([f], .15, rng.uniform(.02, .05)) * rng.uniform(.2, .6), s0, n)
    crunch = band(noise(.25), 600, 3000) * env(int(SR * .25), .002, .07) * .6
    return norm(mix(out, crunch))

def ui_refuel():     # bright power-up arpeggio
    n = .6; out = np.zeros(int(SR * n))
    for i, f in enumerate([523, 659, 784, 1046]):
        out += at(chime([f, f * 2], .3, .12) * .7, i * .06, n)
    return norm(out, .75)


def shadow_swap():    # reverse-whoosh suck -> deep thud -> whisper tail (1.2 s, layered)
    n = 1.2; x = t(n)
    suck = band(noise(.35), 400, 5000) * np.linspace(0, 1, int(SR * .35)) ** 3 * .9
    thud = sweep(70, 32, .45, .6) * env(int(SR * .45), .001, .16) * 1.2
    crack = high(noise(.03), 2000) * env(int(SR * .03), .0004, .008) * .7
    whisper = band(noise(.8), 1500, 6000) * (0.5 + 0.5 * np.sin(2 * np.pi * 9 * t(.8))) * env(int(SR * .8), .05, .3) * .35
    shimmer = chime([392, 466, 587], .7, .3) * .25
    return norm(mix(at(suck, 0, n), at(thud, .33, n), at(crack, .33, n), at(shimmer, .34, n), at(whisper, .4, n)))

SOUNDS = {"shadow/swap": shadow_swap, "soul/feast": soul_feast, "soul/drain": soul_drain, "soul/end": soul_end,
          "shadow/smoke": shadow_smoke, "shadow/backstab": shadow_backstab,
          "blink/step": blink_step, "blink/shatter": blink_shatter, "shield/parry": shield_parry,
          "storm/lunge": storm_lunge, "storm/zap": storm_zap, "frost/slam": frost_slam,
          "frost/shatter": frost_shatter, "ui/refuel": ui_refuel,
          "void/rumble": void_rumble, "void/launch": void_launch, "void/hum": void_hum, "void/collapse": void_collapse,
          "grappler/fire": fire, "grappler/stick": stick, "grappler/reel": reel,
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
