"""Original thriller cue for the promo: 120 BPM, A minor, synced to the edit (numpy only).

Genre: tense psychological-game electronica - staccato string ostinato, a cold piano motif,
four-on-the-floor kick, brass stabs on the hits, glitch stutters and a half-time slow-motion section.
All melody, harmony and patterns here are written for this promo.

render(N, SR) -> (L, R) float arrays, roughly peak 1.
Bars are 2 s long and downbeats fall on even seconds, so every hit/cut in timeline.py lands on a beat.
"""
import numpy as np

BPM = 120
BEAT = 60 / BPM
S16 = BEAT / 4
_PC = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}


def midi(name):
    pc = _PC[name[0]]
    rest = name[1:]
    if rest[0] == "#":
        pc, rest = pc + 1, rest[1:]
    elif rest[0] == "b":
        pc, rest = pc - 1, rest[1:]
    return 12 * (int(rest) + 1) + pc


def hz(m):
    return 440.0 * 2 ** ((m - 69) / 12)


# chord: (root midi in octave 2, minor?)
CH = {"Am": (45, True), "F": (41, False), "Dm": (38, True), "E": (40, False)}
# chord timeline (start sec, chord)
CHORDS = [(0, "Am"), (9, "F"), (11, "E"), (13, "Am"), (16, "E"),
          (18, "Am"), (20, "F"), (22, "Dm"), (24, "E"), (26, "F"), (27, "E"),
          (28, "Dm"), (30, "E"),
          (31, "Am"), (35, "F"), (38, "Dm"), (41.5, "E"),
          (45, "Am"), (46, "F"), (47, "E"),
          (48, "Am"), (50, "F"), (52, "Dm"), (53, "E"),
          (54, "Am"), (56, "F"), (57, "E"), (58, "Am")]


def chord_at(t):
    c = CHORDS[0][1]
    for t0, name in CHORDS:
        if t >= t0 - 1e-6:
            c = name
    return CH[c]


def chord_tones(t, octave_shift=0):
    r, minor = chord_at(t)
    r += 12 * octave_shift
    return [r, r + (3 if minor else 4), r + 7]


# lead motif: 4 bars of (beat offset, note, length in beats)
MOTIF = [(0, "E5", 1), (1, "A5", .5), (1.5, "C6", .5), (2, "B5", 1), (3, "G#5", 1),
         (4, "A5", .5), (4.5, "E5", .5), (5, "F5", 1), (6, "E5", .5), (6.5, "D5", .5), (7, "E5", 1),
         (8, "D6", 1), (9, "C6", .5), (9.5, "B5", .5), (10, "A5", 1), (11, "F5", 1),
         (12, "G#5", 1.5), (13.5, "A5", .5), (14, "B5", 1), (15, "E5", 1)]


class Mix:
    def __init__(self, N, SR):
        self.N, self.SR = N, SR
        self.bus = {k: np.zeros((2, N)) for k in ("drums", "music", "piano")}
        self.kicks = []

    def add(self, bus, sig, t, gain=1.0, pan=0.0):
        i = int(round(t * self.SR))
        if i >= self.N or i + len(sig) <= 0:
            return
        if i < 0:
            sig, i = sig[-i:], 0
        sig = sig[: self.N - i]
        l, r = np.cos((pan + 1) * np.pi / 4) * 1.414, np.sin((pan + 1) * np.pi / 4) * 1.414
        self.bus[bus][0, i:i + len(sig)] += sig * gain * l
        self.bus[bus][1, i:i + len(sig)] += sig * gain * r


def render(N, SR, seed=3):
    rng = np.random.default_rng(seed)
    M = Mix(N, SR)

    def tt(d):
        return np.arange(int(d * SR)) / SR

    def bandpass(x, lo, hi):
        X = np.fft.rfft(x)
        f = np.fft.rfftfreq(len(x), 1 / SR)
        h = 1 / np.sqrt(1 + (f / hi) ** 4) * (1 - 1 / np.sqrt(1 + (f / lo) ** 4))
        return np.fft.irfft(X * h, len(x))

    def saw(f, d, bright, cents=0.0):
        """band-limited saw; bright = harmonic roll-off (acts as the filter cutoff)"""
        x = tt(d)
        f = f * 2 ** (cents / 1200)
        out = np.zeros_like(x)
        ph = rng.uniform(0, 6.28)
        for k in range(1, int(min(48, 16000 / f)) + 1):
            w = np.exp(-(k - 1) / bright) / k
            if w < 2e-3:
                break
            out += w * np.sin(2 * np.pi * f * k * x + ph * k)
        return out

    def env(d, a, dec, sus=0.0, rel=0.02):
        x = tt(d)
        e = np.where(x < a, x / max(a, 1e-4), sus + (1 - sus) * np.exp(-(x - a) / dec))
        nr = int(rel * SR)
        if nr:
            e[-nr:] *= np.linspace(1, 0, nr)
        return e

    # ------------------------------------------------------------ instruments
    def string_stac(t, m, gain, bright, length=0.13):
        f = hz(m)
        for c, p in ((-7, -0.5), (7, 0.5), (0, 0)):
            s = saw(f, length, bright, c) * env(length, 0.004, 0.055, 0.0, 0.01)
            M.add("music", s, t, gain * 0.33, p)

    def bass(t, m, gain, length=0.22, bright=4):
        f = hz(m)
        s = saw(f, length, bright) * 0.7 + np.sin(2 * np.pi * f * tt(length)) * 0.6
        M.add("music", np.tanh(s * env(length, 0.003, 0.12, 0.25, 0.03) * 1.4), t, gain)

    def pad(t, ms, d, gain, bright=2.5):
        for m in ms:
            for c, p in ((-9, -0.7), (9, 0.7)):
                s = saw(hz(m), d, bright, c) * env(d, min(0.6, d / 3), 9e9, 1.0, min(0.8, d / 3))
                M.add("music", s, t, gain / len(ms), p)

    def stab(t, gain=1.0, d=0.6):
        ms = chord_tones(t + 0.01, 1) + chord_tones(t + 0.01, 2)
        for m in ms:
            for c, p in ((-12, -0.6), (12, 0.6)):
                s = saw(hz(m), d, 9, c) * env(d, 0.004, 0.16, 0.0, 0.05)
                M.add("music", s, t, gain * 0.28, p)

    def piano(t, name, gain, d=2.4, pan=-0.15):
        f = hz(midi(name) if isinstance(name, str) else name)
        x = tt(d)
        s = np.zeros_like(x)
        for k in range(1, 9):
            fk = f * k * np.sqrt(1 + 0.0004 * k * k)
            if fk > 15000:
                break
            s += np.sin(2 * np.pi * fk * x) * k ** -1.3 * np.exp(-x * (1.1 + 0.9 * k))
        s += bandpass(rng.standard_normal(len(x)), 1500, 6000) * np.exp(-x * 300) * 0.25  # hammer
        s *= np.minimum(1, x / 0.002)
        M.add("piano", s, t, gain, pan)

    def kick(t, gain=1.0, muffled=False):
        x = tt(0.5)
        f = 44 + 100 * np.exp(-x * 30)
        s = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-x * 6.5)
        s += rng.standard_normal(len(x)) * np.exp(-x * 500) * (0.05 if muffled else 0.25)
        s = np.tanh(s * 1.6)
        if muffled:
            s = bandpass(s, 20, 160)
        M.add("drums", s, t, gain)
        M.kicks.append((t, gain))

    def clap(t, gain=1.0):
        x = tt(0.35)
        nz = rng.standard_normal(len(x))
        e = sum(np.where(x >= o, np.exp(-(x - o) * 110), 0) for o in (0, 0.011, 0.023)) + 0.5 * np.exp(-x * 16)
        s = bandpass(nz, 900, 6000) * e
        M.add("drums", s, t, gain * 0.55, 0.1)

    def snare(t, gain=1.0):
        x = tt(0.22)
        s = bandpass(rng.standard_normal(len(x)), 1500, 8000) * np.exp(-x * 26) * 0.8
        s += np.sin(2 * np.pi * 185 * x) * np.exp(-x * 30) * 0.6
        M.add("drums", s, t, gain * 0.5, -0.05)

    def hat(t, gain=1.0, open_=False):
        d = 0.25 if open_ else 0.06
        x = tt(d)
        s = bandpass(rng.standard_normal(len(x)), 7000, 16000) * np.exp(-x * (14 if open_ else 95))
        M.add("drums", s, t, gain * 0.3, 0.3)

    def crash(t, gain=1.0):
        x = tt(2.6)
        s = bandpass(rng.standard_normal(len(x)), 3500, 15000) * np.exp(-x * 1.6)
        M.add("drums", s, t, gain * 0.22, -0.2)

    def roll(t0, t1, g0=0.2, g1=1.0, step=S16 / 2):
        k = 0
        while t0 + k * step < t1 - 1e-6:
            t = t0 + k * step
            snare(t, g0 + (g1 - g0) * (t - t0) / (t1 - t0))
            k += 1

    def frange(a, b, step):
        return [a + i * step for i in range(int(round((b - a) / step)))]

    # ------------------------------------------------------------ strings ostinato
    # 16th pattern, semitones above the chord root (3 = the chord's third, 1 = flat-2 colour)
    PAT = [0, 0, 7, 0, 1, 0, 7, 0, 12, 0, 7, 0, 3, 0, 7, 3]

    def ostinato(t0, t1, g0, g1, b0, b1, octave=2):
        for t in frange(t0, t1, S16):
            i = int(round(t / S16)) % 16
            r, minor = chord_at(t)
            off = PAT[i]
            if off == 3 and not minor:
                off = 4
            u = (t - t0) / max(t1 - t0, 1e-6)
            acc = 1.0 if i % 4 == 0 else 0.75
            string_stac(t, r + 12 * octave + off, (g0 + (g1 - g0) * u) * acc, b0 + (b1 - b0) * u)

    ostinato(5, 13, 0.12, 0.55, 1.4, 7)
    ostinato(13, 18, 0.55, 0.6, 6, 6)
    ostinato(18, 28, 0.7, 0.75, 8, 9)
    ostinato(45, 48, 0.8, 0.8, 9, 9)
    ostinato(48, 54, 0.85, 0.9, 10, 11)
    ostinato(54, 58, 0.6, 0.45, 7, 3)
    # 0:28-0:31 glitch stutter: repeated notes that tighten and climb, filter closing
    t, step, k = 28.0, S16, 0
    while t < 30.95:
        if t >= 29.0:
            step = S16 / 2
        if t >= 30.0:
            step = S16 / 4
        r, _ = chord_at(t)
        string_stac(t, r + 24 + (k // 8 if t >= 30 else 0), 0.55, max(1.5, 8 - (t - 28) * 2.2), length=step * 0.9)
        t += step
        k += 1

    # ------------------------------------------------------------ bass (8ths, octave pumping)
    def bassline(t0, t1, gain, pattern=(0, 12, 0, 12, 0, 12, 0, 7)):
        for t in frange(t0, t1, BEAT / 2):
            i = int(round(t / (BEAT / 2))) % 8
            r, _ = chord_at(t)
            bass(t, r + pattern[i], gain)

    bassline(13, 18, 0.35)
    bassline(18, 28, 0.55)
    bassline(45, 48, 0.6)
    bassline(48, 54, 0.6)
    bassline(54, 58, 0.45, (0, 0, 0, 12, 0, 0, 0, 12))

    # ------------------------------------------------------------ pads
    pad(0, [33, 45, 52], 5.3, 0.22, 1.6)                                # cold open drone (A)
    for t0, t1 in [(31, 35), (35, 38), (38, 41.5), (41.5, 45)]:          # slow-motion strings
        pad(t0, [m + 12 for m in chord_tones(t0 + 0.01)] + [chord_tones(t0 + 0.01)[0] + 24], t1 - t0 + 0.4, 0.42, 2.2)
    for t0, t1 in [(48, 50), (50, 52), (52, 53), (53, 54)]:
        pad(t0, [m + 24 for m in chord_tones(t0 + 0.01)], t1 - t0 + 0.2, 0.22, 3)
    pad(58, [33, 45, 52, 57, 60, 64], 6.0, 0.35, 2.4)

    # ------------------------------------------------------------ brass stabs on the hits
    for h in (5.0, 13.0, 18.0, 28.0, 45.0, 48.0, 54.0, 58.0):
        stab(h, 1.0 if h in (13.0, 48.0, 58.0) else 0.75, 0.9 if h in (13.0, 58.0) else 0.6)
    for h in (46.0, 47.0):                                               # montage cuts
        stab(h, 0.5, 0.35)

    # ------------------------------------------------------------ drums
    for t in frange(9, 13, BEAT):
        kick(t, 0.55 + 0.1 * (t - 9) / 4)
    for t in frange(11, 13, S16):
        hat(t, 0.4 if int(round(t / S16)) % 2 else 0.15)
    roll(12, 13, 0.1, 0.8)
    # title: half-time pulse
    for t in frange(13, 18, BEAT):
        kick(t, 0.75 if int(round(t / BEAT)) % 2 == 0 else 0.45)
        hat(t + BEAT / 2, 0.35)
    roll(17, 18, 0.15, 0.9)
    crash(13, 1.0)
    # rule: full groove
    crash(18, 1.0)
    for t in frange(18, 28, BEAT):
        b = int(round(t / BEAT)) % 4
        kick(t, 0.9)
        if b in (1, 3):
            clap(t, 0.9)
    for t in frange(18, 28, S16):
        i = int(round(t / S16)) % 4
        hat(t, (0.5, 0.18, 0.7, 0.18)[i], open_=(i == 2 and int(round(t / S16)) % 16 == 14))
    roll(27, 28, 0.2, 1.0)
    kick(28.0, 1.0)
    crash(28, 0.8)
    for t in frange(30, 31, S16):                                        # stutter kicks into the tape stop
        kick(t, 0.35 + 0.4 * (t - 30))
    # slow motion: muffled heartbeat-kick on each downbeat, then a long build
    for t in frange(35, 43, 2 * BEAT):
        kick(t, 0.8, muffled=True)
        kick(t + 0.28, 0.5, muffled=True)
    roll(43, 45, 0.05, 0.9, S16)
    # montage: full groove, 16th kick fill at the end
    crash(45, 1.0)
    for t in frange(45, 47.5, BEAT):
        kick(t, 0.95)
        if int(round(t / BEAT)) % 2:
            clap(t, 0.9)
    for t in frange(47.5, 48, S16):
        kick(t, 0.6)
    for t in frange(45, 48, S16):
        hat(t, 0.55 if int(round(t / S16)) % 2 else 0.25)
    # cards: climax
    crash(48, 1.1)
    for t in frange(48, 54, BEAT):
        kick(t, 1.0)
        if int(round(t / BEAT)) % 2:
            clap(t, 1.0)
    for t in frange(48, 53, S16):
        i = int(round(t / S16)) % 4
        hat(t, (0.5, 0.2, 0.75, 0.2)[i])
    roll(53, 54, 0.2, 1.0, S16 / 2)
    # key art: half-time, thinning out
    crash(54, 0.9)
    for t in frange(54, 57, 2 * BEAT):
        kick(t, 0.8)
        clap(t + BEAT, 0.6)
    for t in frange(54, 57, BEAT / 2):
        hat(t, 0.3)
    roll(57, 58, 0.1, 0.9, S16 / 2)
    kick(58.0, 1.0)
    crash(58, 1.2)

    # ------------------------------------------------------------ piano motif
    def motif(t0, bars, gain, transpose=0, speed=1.0):
        for b, name, ln in MOTIF:
            if b < bars[0] * 4 or b >= bars[1] * 4:
                continue
            piano(t0 + (b - bars[0] * 4) * BEAT / speed, midi(name) + transpose, gain, d=max(1.0, ln * 1.6))

    for t, n in [(1.0, "A4"), (2.0, "C5"), (3.0, "B4"), (4.0, "G#4")]:  # cold open, under the clock
        piano(t, n, 0.45, d=2.5)
    motif(14, (0, 2), 0.45)
    motif(18, (0, 4), 0.55)
    motif(26, (0, 1), 0.5)
    for t, n in [(32.0, "E6"), (33.0, "A5"), (34.13, "C6"), (36.0, "B5"), (37.0, "G#5"),
                 (39.0, "A5"), (40.0, "F5"), (41.5, "E5"), (43.0, "B5"), (44.0, "G#5")]:
        piano(t, n, 0.5, d=3.0, pan=0.1)                                 # slow motion: lonely high notes
    motif(48, (0, 3), 0.5, transpose=12)
    motif(54, (2, 4), 0.42)
    for t, n in [(58.0, "A4"), (58.0, "E5"), (58.0, "A5"), (59.5, "C6"), (61.0, "B5"), (62.0, "A5")]:
        piano(t, n, 0.42, d=3.5)

    # ------------------------------------------------------------ sidechain the music to the kicks
    duck = np.ones(N)
    x = np.arange(int(0.3 * SR)) / SR
    shape = 0.6 * np.exp(-x / 0.09)
    for t, g in M.kicks:
        i = int(t * SR)
        seg = shape[: max(0, N - i)] * min(1.0, g)
        duck[i:i + len(seg)] -= seg
    duck = np.clip(duck, 0.35, 1)
    music = M.bus["music"] * duck

    # ------------------------------------------------------------ piano reverb (long, dark)
    ir_n = int(3.2 * SR)
    irx = np.arange(ir_n) / SR
    piano_wet = np.zeros_like(M.bus["piano"])
    for c in range(2):
        ir = rng.standard_normal(ir_n) * np.exp(-irx * 1.9)
        ir = bandpass(ir, 200, 5000)
        ir[: int(0.02 * SR)] = 0
        m = N + ir_n
        nfft = 1 << (m - 1).bit_length()
        piano_wet[c] = np.fft.irfft(np.fft.rfft(M.bus["piano"][c], nfft) * np.fft.rfft(ir, nfft), nfft)[:N]
    piano_wet *= np.abs(M.bus["piano"]).max() / max(np.abs(piano_wet).max(), 1e-9) * 0.5
    piano_bus = M.bus["piano"] + piano_wet

    out = M.bus["drums"] * 1.0 + music * 0.95 + piano_bus * 0.5
    return out[0], out[1], {"drums": M.bus["drums"], "music": music, "piano": piano_bus}
