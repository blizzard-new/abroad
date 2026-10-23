"""Background music for generated videos, synthesised so it carries no licensing strings.

Same idea as marketing/promo-video/music.py, but driven by a script's scene timings instead of fixed presets:
the beat drops after the hook, every scene change gets a soft whoosh, and the last chord rings under the end card.
Instagram's API cannot attach the in-app trending audio, so the music is baked into the MP4.
"""

from __future__ import annotations

import wave
from pathlib import Path

import numpy as np

SR = 44100
BPM = 112
BEAT = 60 / BPM
BAR = 4 * BEAT
CHORDS = [[48, 55, 60, 64, 67], [43, 50, 59, 62, 67], [45, 52, 57, 60, 64], [41, 48, 57, 60, 65]]


def _hz(note: float) -> float:
    return 440.0 * 2 ** ((note - 69) / 12)


def _env(length: float, attack: float, release: float) -> np.ndarray:
    m = int(length * SR)
    e = np.ones(m)
    a = min(m, max(1, int(attack * SR)))
    r = min(m, max(1, int(release * SR)))
    e[:a] = np.linspace(0, 1, a)
    e[-r:] *= np.linspace(1, 0, r)
    return e


def _smooth(x: np.ndarray, width: int) -> np.ndarray:
    return np.convolve(x, np.ones(width) / width, mode="same")


def soundtrack(duration: float, cues: list[float], out: Path, *, drums_in: float = 3.0, seed: int = 7) -> Path:
    rng = np.random.default_rng(seed)
    n = int(SR * (duration + 0.5))
    left, right = np.zeros(n), np.zeros(n)
    end_hit = cues[-1] if cues else max(0.0, duration - 5)

    def add(sig: np.ndarray, start: float, gain: float = 1.0, pan: float = 0.0) -> None:
        i = int(start * SR)
        if i >= n or i < 0:
            return
        sig = sig[: n - i] * gain
        left[i : i + len(sig)] += sig * np.sqrt(0.5 * (1 - pan))
        right[i : i + len(sig)] += sig * np.sqrt(0.5 * (1 + pan))

    def pad(notes: list[int], length: float) -> np.ndarray:
        tt = np.arange(int(length * SR)) / SR
        sig = np.zeros_like(tt)
        for note in notes[1:]:
            for detune in (-0.12, 0.0, 0.12):
                f = _hz(note + detune)
                for k in range(1, 5):
                    sig += np.sin(2 * np.pi * f * k * tt + k) / (k * 1.6)
        return sig * _env(length, 0.35, 0.6) / 30

    def pluck(note: int, length: float = 0.5) -> np.ndarray:
        tt = np.arange(int(length * SR)) / SR
        f = _hz(note)
        sig = np.sin(2 * np.pi * f * tt) + 0.35 * np.sin(4 * np.pi * f * tt)
        return sig * np.exp(-tt * 9) * _env(length, 0.004, 0.05)

    def bass(note: int, length: float) -> np.ndarray:
        tt = np.arange(int(length * SR)) / SR
        f = _hz(note - 12)
        return (np.sin(2 * np.pi * f * tt) + 0.25 * np.sin(4 * np.pi * f * tt)) * np.exp(-tt * 2.2) * _env(length, 0.01, 0.08)

    def kick() -> np.ndarray:
        tt = np.arange(int(0.35 * SR)) / SR
        return np.sin(2 * np.pi * np.cumsum(45 + 90 * np.exp(-tt * 30)) / SR) * np.exp(-tt * 9)

    def noise_burst(length: float, decay: float, smooth: int) -> np.ndarray:
        noise = rng.standard_normal(int(length * SR))
        bright = noise - _smooth(noise, smooth)
        return bright * np.exp(-np.arange(len(noise)) / SR * decay)

    def whoosh(length: float = 0.7) -> np.ndarray:
        noise = rng.standard_normal(int(length * SR))
        tt = np.arange(len(noise)) / SR
        return (noise - _smooth(noise, 40)) * np.sin(np.pi * tt / length) ** 2 * 0.5

    for b in range(int(duration / BAR) + 1):
        start = b * BAR
        chord = CHORDS[b % 4]
        add(pad(chord, BAR + 0.5), start, 0.55)
        arp = [chord[2], chord[3], chord[4], chord[3] + 12 if b % 2 else chord[4] + 5, chord[2] + 12, chord[4], chord[3], chord[4]]
        for i, note in enumerate(arp):
            at = start + i * BEAT / 2
            add(pluck(note + 12), at, 0.16 if at < drums_in else 0.22, pan=-0.35 if i % 2 else 0.35)
        if start >= drums_in - 0.01:
            add(bass(chord[0], BEAT * 2), start, 0.55)
            add(bass(chord[0], BEAT * 2), start + 2 * BEAT, 0.45)

    for i in range(int(duration / BEAT)):
        at = i * BEAT
        if at < drums_in - 0.01 or at > end_hit + 4 * BEAT:
            continue
        add(kick(), at, 0.75)
        if i % 2 == 1:
            add(noise_burst(0.18, 28, 12), at, 0.25)
        add(noise_burst(0.05, 70, 4), at + BEAT / 2, 0.12, pan=0.3)

    for cue in cues:
        add(whoosh(), cue - 0.35, 0.22)
    add(pad([0, 48, 52, 55, 60, 64, 67], 6.5), end_hit + 0.4, 0.6)
    add(pluck(84, 1.6), end_hit + 0.4, 0.25)

    mix = np.stack([left, right], axis=1)[: int(SR * duration)]
    fade = np.ones(len(mix))
    fade[: int(0.4 * SR)] = np.linspace(0, 1, int(0.4 * SR))
    tail = min(len(mix), int(2.5 * SR))
    fade[-tail:] = np.linspace(1, 0, tail) ** 1.5
    mix *= fade[:, None]
    mix = np.tanh(mix * 1.4) / np.tanh(1.4)
    mix /= max(np.max(np.abs(mix)), 1e-9) / 0.89
    with wave.open(str(out), "wb") as handle:
        handle.setnchannels(2)
        handle.setsampwidth(2)
        handle.setframerate(SR)
        handle.writeframes((mix * 32767).astype("<i2").tobytes())
    return out
