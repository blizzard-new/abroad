"""Background music and sound effects for the UniWay promo video (65 s, 44.1 kHz stereo WAV).

Everything is synthesised here, so the soundtrack has no licensing strings attached. The cue times match the scene
changes in index.html; if the timeline there moves, move CUES / POPS below with it.

    python3 marketing/promo-video/music.py marketing/promo-video/build/music.wav
    python3 marketing/promo-video/music.py marketing/promo-video/build/music-reels.wav reels
"""

import sys
import wave

import numpy as np

SR = 44100
BPM = 112
BEAT = 60 / BPM
BAR = 4 * BEAT

# One timing per video: index.html (landscape) and reels.html (vertical, for Instagram Reels).
#   drums_in: the beat starts when the logo appears; end_hit: the end card;
#   cues: scene changes (a soft whoosh); pops: the mascot starts talking (a little blip).
PRESETS = {
    "landscape": {
        "duration": 65.0, "drums_in": 6.3, "end_hit": 58.0,
        "cues": [6.3, 10.0, 17.0, 22.6, 29.0, 36.0, 42.0, 48.0, 53.2, 58.0],
        "pops": [2.8, 7.9, 11.2, 17.8, 23.6, 30.2, 37.2, 43.2, 49.6, 54.6],
    },
    "reels": {
        "duration": 36.0, "drums_in": 3.0, "end_hit": 31.0,
        "cues": [3.0, 5.6, 11.6, 17.0, 22.5, 27.0, 31.0],
        "pops": [0.8, 3.9, 27.8],
    },
}
preset = PRESETS[sys.argv[2] if len(sys.argv) > 2 else "landscape"]
DURATION = preset["duration"]
DRUMS_IN = preset["drums_in"]
END_HIT = preset["end_hit"]
CUES = preset["cues"]
POPS = preset["pops"]

# I - V - vi - IV in C major, as MIDI notes.
CHORDS = [[48, 55, 60, 64, 67], [43, 50, 59, 62, 67], [45, 52, 57, 60, 64], [41, 48, 57, 60, 65]]

rng = np.random.default_rng(7)
n = int(SR * DURATION)
t = np.arange(n) / SR
left = np.zeros(n)
right = np.zeros(n)


def hz(note):
    return 440.0 * 2 ** ((note - 69) / 12)


def add(sig, start, gain=1.0, pan=0.0):
    i = int(start * SR)
    if i >= n:
        return
    sig = sig[: n - i] * gain
    left[i : i + len(sig)] += sig * np.sqrt(0.5 * (1 - pan))
    right[i : i + len(sig)] += sig * np.sqrt(0.5 * (1 + pan))


def env(length, attack, release):
    m = int(length * SR)
    e = np.ones(m)
    a = max(1, int(attack * SR))
    r = max(1, int(release * SR))
    e[:a] = np.linspace(0, 1, a)
    e[-r:] *= np.linspace(1, 0, r)
    return e


def lowpass(x, cutoff):
    # One-pole low-pass, run twice for a gentler 12 dB/oct slope.
    a = np.exp(-2 * np.pi * cutoff / SR)
    for _ in range(2):
        y = np.empty_like(x)
        acc = 0.0
        for i, v in enumerate(x):
            acc = (1 - a) * v + a * acc
            y[i] = acc
        x = y
    return x


def pad(notes, length):
    m = int(length * SR)
    tt = np.arange(m) / SR
    sig = np.zeros(m)
    for note in notes[1:]:
        for detune in (-0.12, 0.0, 0.12):
            f = hz(note + detune)
            # A soft saw made of its first few harmonics.
            for k in range(1, 6):
                sig += np.sin(2 * np.pi * f * k * tt + k) / (k * 1.6)
    return sig * env(length, 0.35, 0.6) / 30


def pluck(note, length=0.5):
    m = int(length * SR)
    tt = np.arange(m) / SR
    f = hz(note)
    sig = np.sin(2 * np.pi * f * tt) + 0.35 * np.sin(4 * np.pi * f * tt) + 0.12 * np.sin(6 * np.pi * f * tt)
    return sig * np.exp(-tt * 9) * env(length, 0.004, 0.05)


def bass(note, length):
    m = int(length * SR)
    tt = np.arange(m) / SR
    f = hz(note - 12)
    sig = np.sin(2 * np.pi * f * tt) + 0.25 * np.sin(4 * np.pi * f * tt)
    return sig * np.exp(-tt * 2.2) * env(length, 0.01, 0.08)


def kick():
    m = int(0.35 * SR)
    tt = np.arange(m) / SR
    phase = 2 * np.pi * np.cumsum(45 + 90 * np.exp(-tt * 30)) / SR
    return np.sin(phase) * np.exp(-tt * 9)


def hat(length=0.05):
    m = int(length * SR)
    noise = rng.standard_normal(m)
    noise = noise - lowpass(noise.copy(), 6000)
    return noise * np.exp(-np.arange(m) / SR * 70)


def clap():
    m = int(0.18 * SR)
    noise = rng.standard_normal(m)
    noise = lowpass(noise, 3500) - lowpass(noise.copy(), 900)
    tt = np.arange(m) / SR
    return noise * (np.exp(-tt * 28) + 0.6 * np.exp(-np.maximum(tt - 0.012, 0) * 30) * (tt > 0.012))


def whoosh(length=0.7):
    m = int(length * SR)
    noise = rng.standard_normal(m)
    tt = np.arange(m) / SR
    shape = np.sin(np.pi * tt / length) ** 2
    return (noise - lowpass(noise.copy(), 900)) * shape * 0.5


def blip():
    m = int(0.16 * SR)
    tt = np.arange(m) / SR
    phase = 2 * np.pi * np.cumsum(700 + 900 * tt / 0.16) / SR
    return np.sin(phase) * np.exp(-tt * 22)


def riser(length):
    m = int(length * SR)
    tt = np.arange(m) / SR
    noise = rng.standard_normal(m)
    noise = noise - lowpass(noise.copy(), 1500)
    return noise * (tt / length) ** 2 * 0.6


# Harmony: one chord per bar, the whole way through.
bars = int(DURATION / BAR) + 1
for b in range(bars):
    start = b * BAR
    chord = CHORDS[b % 4]
    add(pad(chord, BAR + 0.5), start, 0.55)
    # Eighth-note arpeggio; quieter during the hook so the beat drop lands.
    arp = [chord[2], chord[3], chord[4], chord[3] + 12 if b % 2 else chord[4] + 5, chord[2] + 12, chord[4], chord[3], chord[4]]
    for i, note in enumerate(arp):
        at = start + i * BEAT / 2
        level = 0.16 if at < DRUMS_IN else 0.22
        add(pluck(note + 12), at, level, pan=-0.35 if i % 2 else 0.35)
    if start >= DRUMS_IN - 0.01:
        add(bass(chord[0], BEAT * 2), start, 0.55)
        add(bass(chord[0], BEAT * 2), start + 2 * BEAT, 0.45)

# Drums from the logo onwards; they drop out under the end card so it can breathe.
beat_count = int(DURATION / BEAT)
for i in range(beat_count):
    at = i * BEAT
    if at < DRUMS_IN - 0.01 or at > END_HIT + 4 * BEAT:
        continue
    add(kick(), at, 0.75)
    if i % 2 == 1:
        add(clap(), at, 0.3)
    add(hat(), at + BEAT / 2, 0.12, pan=0.3)
    add(hat(0.03), at, 0.06, pan=-0.3)

add(riser(1.6), DRUMS_IN - 1.6, 0.35)
for c in CUES:
    add(whoosh(), c - 0.35, 0.22)
for p in POPS:
    add(blip(), p, 0.13)

# A final chord rings out under the end card.
add(pad([0, 48, 52, 55, 60, 64, 67], 6.5), END_HIT + 0.4, 0.6)
add(pluck(84, 1.6), END_HIT + 0.4, 0.25)
add(pluck(79, 1.6), END_HIT + 0.55, 0.2)

mix = np.stack([left, right], axis=1)
# Fade in/out, gentle limiting, normalise.
fade = np.ones(n)
fade[: int(0.4 * SR)] = np.linspace(0, 1, int(0.4 * SR))
fade_out = int(3.0 * SR)
fade[-fade_out:] = np.linspace(1, 0, fade_out) ** 1.5
mix *= fade[:, None]
mix = np.tanh(mix * 1.4) / np.tanh(1.4)
mix /= np.max(np.abs(mix)) / 0.89

out = sys.argv[1] if len(sys.argv) > 1 else "music.wav"
with wave.open(out, "wb") as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes((mix * 32767).astype("<i2").tobytes())
print(f"wrote {out}")
