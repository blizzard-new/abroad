"""Soundtrack for the tutorial video: quiet background music and a soft tick on every click (44.1 kHz stereo WAV).

Everything is synthesised here, so there is nothing to license. record.py calls it with the timeline it wrote,
which holds the video's length and the moment of each click:

    python3 marketing/tutorial-video/music.py marketing/tutorial-video/build/timeline.json build/tutorial-music.wav
"""

import json
import sys
import wave

import numpy as np

SR = 44100
BPM = 84
BEAT = 60 / BPM
BAR = 4 * BEAT

timeline = json.load(open(sys.argv[1]))
DURATION = float(timeline["duration"])
CLICKS = timeline["clicks"]

# I - vi - IV - V in C major, voiced low and open so it stays under the viewer's reading.
CHORDS = [[48, 55, 64, 67], [45, 52, 60, 64], [41, 48, 57, 60], [43, 50, 59, 62]]
ARP = [0, 2, 1, 3, 2, 1]

rng = np.random.default_rng(11)
n = int(SR * DURATION)
left = np.zeros(n)
right = np.zeros(n)


def hz(note):
    return 440.0 * 2 ** ((note - 69) / 12)


def add(sig, start, gain=1.0, pan=0.0):
    i = int(start * SR)
    if i >= n or i < 0:
        return
    sig = sig[: n - i] * gain
    left[i : i + len(sig)] += sig * (1 - pan) / 2 ** 0.5
    right[i : i + len(sig)] += sig * (1 + pan) / 2 ** 0.5


def pad(notes, length):
    t = np.arange(int(SR * length)) / SR
    sig = sum(np.sin(2 * np.pi * hz(m) * t + np.sin(2 * np.pi * 0.21 * t) * 0.4) for m in notes)
    sig += 0.3 * sum(np.sin(2 * np.pi * hz(m + 12) * t * 1.003) for m in notes)
    env = np.minimum(1, t / 1.2) * np.minimum(1, (length - t) / 1.2)
    return sig * env / len(notes)


def pluck(note, length=1.4):
    t = np.arange(int(SR * length)) / SR
    f = hz(note)
    sig = np.sin(2 * np.pi * f * t) + 0.35 * np.sin(4 * np.pi * f * t) + 0.12 * np.sin(6 * np.pi * f * t)
    return sig * np.exp(-t * 3.2) * np.minimum(1, t / 0.006)


def tick():
    t = np.arange(int(SR * 0.05)) / SR
    body = np.sin(2 * np.pi * 1850 * t) * np.exp(-t * 140)
    noise = rng.standard_normal(len(t)) * np.exp(-t * 320) * 0.35
    return body + noise


bars = int(DURATION / BAR) + 1
for b in range(bars):
    chord = CHORDS[b % len(CHORDS)]
    add(pad(chord, BAR + 1.0), b * BAR, 0.16)
    add(pluck(chord[0] - 12, 2.4), b * BAR, 0.10)
    for k in range(6):
        note = chord[ARP[k]] + 12
        add(pluck(note), b * BAR + k * (BAR / 6), 0.055, pan=0.25 if k % 2 else -0.25)

for c in CLICKS:
    add(tick(), c, 0.22)

mix = np.stack([left, right], axis=1)
fade = np.ones(n)
fade[: int(1.0 * SR)] = np.linspace(0, 1, int(1.0 * SR))
fade_out = int(3.0 * SR)
fade[-fade_out:] = np.linspace(1, 0, fade_out) ** 1.5
mix *= fade[:, None]
mix = np.tanh(mix * 1.2) / np.tanh(1.2)
mix /= np.max(np.abs(mix)) / 0.7

with wave.open(sys.argv[2], "wb") as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes((mix * 32767).astype("<i2").tobytes())
print(f"wrote {sys.argv[2]}")
