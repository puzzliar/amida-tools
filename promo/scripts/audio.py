"""Synthesised score + SFX for the promo (numpy only). Writes a 48 kHz stereo WAV."""
import sys, os, wave
import numpy as np
sys.path.insert(0, os.path.dirname(__file__))
from timeline import *

SR = 48000
DUR = TOTAL / FPS
N = int(SR * DUR)
t = np.arange(N) / SR
rng = np.random.default_rng(7)
L = np.zeros(N)
R = np.zeros(N)


def add(sig, start, gain=1.0, pan=0.0):
    i = int(start * SR)
    if i >= N:
        return
    sig = sig[: N - i]
    l = np.cos((pan + 1) * np.pi / 4)
    r = np.sin((pan + 1) * np.pi / 4)
    L[i:i + len(sig)] += sig * gain * l * 1.414
    R[i:i + len(sig)] += sig * gain * r * 1.414


def onepole(x, fc):
    a = np.exp(-2 * np.pi * fc / SR)
    y = np.empty_like(x)
    acc = 0.0
    # vectorised IIR via lfilter-like loop in chunks (numpy only)
    from itertools import accumulate
    out = np.fromiter(accumulate(x * (1 - a), lambda p, v: p * a + v), float, len(x))
    return out


def lowpass(x, fc):
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / SR)
    return np.fft.irfft(X / np.sqrt(1 + (f / fc) ** 4), len(x))


def bandpass(x, lo, hi):
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / SR)
    h = 1 / np.sqrt(1 + (f / hi) ** 4) * (1 - 1 / np.sqrt(1 + (f / lo) ** 4))
    return np.fft.irfft(X * h, len(x))


def env(n, a, d, sus=None):
    e = np.ones(n)
    na = max(1, int(a * SR))
    e[:na] = np.linspace(0, 1, na)
    e[na:] = np.exp(-np.arange(n - na) / (d * SR))
    return e


def smoothstep(x):
    x = np.clip(x, 0, 1)
    return x * x * (3 - 2 * x)


# ---------------------------------------------------------------- drone bed
def saw(f, tt, harm=14):
    s = np.zeros_like(tt)
    for k in range(1, harm):
        s += np.sin(2 * np.pi * f * k * tt) / k
    return s


bed = np.zeros(N)
for f, g in [(55.0, 1.0), (55.3, 0.8), (82.41, 0.45), (58.27, 0.25), (110.0, 0.25)]:
    bed += saw(f, t) * g
lfo = 0.5 + 0.5 * np.sin(2 * np.pi * 0.07 * t)
bed = lowpass(bed, 260) * (0.6 + 0.4 * lfo)
bed_env = np.interp(t, [0, 4.5, 5, 13, 18, 28, 37, 48, 54, 57.8, 58, 62, 64],
                    [0.25, 0.4, 0.55, 0.55, 0.6, 0.65, 0.75, 0.6, 0.45, 0.2, 0.75, 0.55, 0.0])
bed *= bed_env * 0.10
L += bed
R += np.roll(bed, 300)

# high tension cluster (strings-ish) under montage & screens
cl = np.zeros(N)
for f in [880.0, 932.3, 1318.5]:
    cl += np.sin(2 * np.pi * f * t + 3 * np.sin(2 * np.pi * 5.5 * t)) * 0.33
trem = 0.6 + 0.4 * np.sin(2 * np.pi * 7 * t)
cl_env = np.interp(t, [0, 28, 32, 37, 46, 48, 49, 64], [0, 0, 0.25, 0.45, 0.9, 0.0, 0, 0])
cl = lowpass(cl * trem * cl_env, 3000) * 0.025
L += cl
R += np.roll(cl, 700)

# ---------------------------------------------------------------- clock ticks
for k, s in enumerate(np.arange(TICKS[0] + 0.35, TICKS[1], 0.5)):
    n = int(0.06 * SR)
    nz = rng.standard_normal(n)
    tick = bandpass(nz, 1800, 6000) * env(n, 0.0005, 0.008)
    tick += np.sin(2 * np.pi * (2400 if k % 2 else 1900) * np.arange(n) / SR) * env(n, 0.0005, 0.01) * 0.4
    add(tick, s, 0.35 + 0.1 * (k / 10), pan=-0.3 if k % 2 else 0.3)


# ---------------------------------------------------------------- impacts
def boom(dur=3.5, big=1.0):
    n = int(dur * SR)
    tt = np.arange(n) / SR
    f = 30 + 70 * np.exp(-tt * 9)
    ph = 2 * np.pi * np.cumsum(f) / SR
    s = np.sin(ph) * np.exp(-tt * 1.4) * 1.0
    nz = lowpass(rng.standard_normal(n), 900) * np.exp(-tt * 7) * 0.9
    metal = np.zeros(n)
    for fr in [311, 467, 622, 893, 1244]:
        metal += np.sin(2 * np.pi * fr * tt + rng.uniform(0, 6)) * np.exp(-tt * (2.5 + fr / 500))
    return (s + nz + metal * 0.07 * big) * big


for h in HITS:
    big = 1.25 if h in (13.0, 58.0) else 1.0
    add(boom(big=big), h - 0.01, 0.55)


# ---------------------------------------------------------------- risers
def riser(d):
    n = int(d * SR)
    tt = np.arange(n) / SR
    x = tt / d
    nz = rng.standard_normal(n)
    out = np.zeros(n)
    seg = 4096
    for i in range(0, n, seg):
        c = 300 + 5000 * x[i] ** 2
        out[i:i + seg] = bandpass(nz[i:i + seg], c * 0.6, c * 1.6)[: len(out[i:i + seg])]
    tone = np.sin(2 * np.pi * np.cumsum(220 + 660 * x ** 2) / SR) * 0.25
    return (out + tone) * x ** 2.2


for a, b in RISERS:
    add(riser(b - a), a, 0.32)


# ---------------------------------------------------------------- ostinato (plucked minor pattern)
def pluck(f, d=0.5):
    n = int(d * SR)
    tt = np.arange(n) / SR
    s = np.zeros(n)
    for k, g in [(1, 1), (2, 0.5), (3, 0.25), (4, 0.12)]:
        s += np.sin(2 * np.pi * f * k * tt) * g * np.exp(-tt * (6 + 3 * k))
    return s * env(n, 0.002, 0.25)


A2, Bb2, C3, E3, D3, F3 = 110.0, 116.54, 130.81, 164.81, 146.83, 174.61
pattern = [A2, A2, C3, A2, Bb2, A2, E3, A2, A2, A2, C3, A2, F3, E3, Bb2, A2]
bpm = 112
step = 60 / bpm / 2
s0, s1 = OSTINATO
i = 0
tt = s0
while tt < s1 - 0.05:
    prog = (tt - s0) / (s1 - s0)
    g = 0.10 + 0.14 * prog
    if 28 <= tt < 29.0 or 45 <= tt < 45.6:
        g *= 0.2
    elif SLOWMO[0] <= tt < SLOWMO[1]:
        g *= 0.22  # the beat falls away under the slow-motion footage
    add(pluck(pattern[i % 16]), tt, g, pan=-0.25 if i % 2 else 0.25)
    add(pluck(pattern[i % 16] * 2, 0.3), tt, g * 0.35, pan=0.4 if i % 2 else -0.4)
    i += 1
    tt += step

# ---------------------------------------------------------------- heartbeat
hb0, hb1 = HEART
tt = hb0 + 0.25
k = 0
while tt < hb1 - 0.3:
    for off, g in [(0, 1.0), (0.22, 0.7)]:
        n = int(0.4 * SR)
        x = np.arange(n) / SR
        s = np.sin(2 * np.pi * (48 + 30 * np.exp(-x * 30)) * x) * np.exp(-x * 11)
        add(s, tt + off, 0.7 * g)
    tt += 60 / (66 + k * 6)
    k += 1

# ---------------------------------------------------------------- whooshes on montage cuts
for c in MONTAGE_CUTS:
    d = 0.45
    n = int(d * SR)
    x = np.linspace(0, 1, n)
    w = bandpass(rng.standard_normal(n), 400, 4000) * np.sin(np.pi * x) ** 2 * x
    add(w, c - d * 0.8, 0.22, pan=rng.uniform(-0.5, 0.5))

# ---------------------------------------------------------------- slow-motion section: tape-stop, static, slowed pulse
sm0, sm1 = SLOWMO
# tape-stop into slow motion: a bright chord whose pitch sags and dies
n = int(1.1 * SR)
x = np.arange(n) / SR
fall = np.cumsum(np.interp(x, [0, 1.1], [1.0, 0.12]) ** 1.5) / SR
ts = sum(np.sin(2 * np.pi * f * fall) for f in (220, 261.63, 329.63)) * np.interp(x, [0, 0.05, 0.9, 1.1], [0, 1, 0.6, 0])
add(lowpass(ts, 2500), sm0 - 0.55, 0.16)
# crackling static bed
n = int((sm1 - sm0) * SR)
x = np.arange(n) / SR
hiss = bandpass(rng.standard_normal(n), 2500, 9000) * 0.25
clicks = (rng.random(n) > 0.9993) * rng.standard_normal(n) * 6
crackle = hiss + lowpass(clicks, 6000)
add(crackle * np.interp(x, [0, 0.4, n / SR - 1.0, n / SR], [0, 1, 1, 0]), sm0, 0.10, pan=-0.2)
add(np.roll(crackle, 9000) * np.interp(x, [0, 0.4, n / SR - 1.0, n / SR], [0, 1, 1, 0]), sm0, 0.10, pan=0.2)
# static bursts on the picture glitches
for gt in GLITCH_TIMES:
    n = int(0.12 * SR)
    b = bandpass(rng.standard_normal(n), 800, 7000) * env(n, 0.002, 0.05)
    b += np.sign(np.sin(2 * np.pi * 60 * np.arange(n) / SR)) * env(n, 0.002, 0.04) * 0.3  # mains buzz
    add(b, gt, 0.45, pan=rng.uniform(-0.6, 0.6))
# slowed, sub-heavy pulse under the handovers (like a heartbeat heard underwater)
tt = 38.0
while tt < sm1 - 0.4:
    n = int(0.9 * SR)
    x = np.arange(n) / SR
    s = np.sin(2 * np.pi * (38 + 20 * np.exp(-x * 12)) * x) * np.exp(-x * 4.5)
    add(lowpass(s, 180), tt, 0.55)
    tt += 60 / 52

# ---------------------------------------------------------------- final chord
n = int(6 * SR)
x = np.arange(n) / SR
ch = np.zeros(n)
for f in [110, 164.81, 220, 261.63, 329.63, 493.88]:
    ch += saw(f, x, 8) * 0.18
ch = lowpass(ch, 1400) * smoothstep(x / 0.6) * np.interp(x, [0, 3.5, 6], [1, 0.7, 0])
add(ch, 58.0, 0.10)

# ---------------------------------------------------------------- reverb + master
ir_n = int(2.4 * SR)
irx = np.arange(ir_n) / SR
irL = rng.standard_normal(ir_n) * np.exp(-irx * 2.6)
irR = rng.standard_normal(ir_n) * np.exp(-irx * 2.6)
irL[0] = irR[0] = 0


def conv(x, h):
    m = len(x) + len(h)
    nfft = 1 << (m - 1).bit_length()
    return np.fft.irfft(np.fft.rfft(x, nfft) * np.fft.rfft(h, nfft), nfft)[: len(x)]


wetL = conv(L, irL) * 0.012
wetR = conv(R, irR) * 0.012
L2 = L + wetL
R2 = R + wetR
fade = np.interp(t, [0, 0.05, DUR - 2.0, DUR], [0, 1, 1, 0])
L2 *= fade
R2 *= fade
pk = max(np.abs(L2).max(), np.abs(R2).max())
L2 = np.tanh(L2 / pk * 1.15) / np.tanh(1.15) * 0.89
R2 = np.tanh(R2 / pk * 1.15) / np.tanh(1.15) * 0.89
out = np.stack([L2, R2], 1)
pcm = (out * 32767).astype("<i2")
path = sys.argv[1]
with wave.open(path, "wb") as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes(pcm.tobytes())
print("wrote", path, DUR, "s")
