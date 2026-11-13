"""Builds the 30-second narration track for opening-v2.html.

Each line of narration.txt is synthesised with Google Text-to-Speech (zh-TW),
trimmed, sped up 1.25x without changing pitch, placed on a timeline and mixed
into one 30-second mono track. The line timings are written to
out/narration.json so the storyboard can sync captions and animations.

    python3 docs/cgu-demo/video/narration.py

Needs: pip install gTTS, and ffmpeg/ffprobe on PATH. Behind a TLS-inspecting
proxy set REQUESTS_CA_BUNDLE to its CA bundle.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

from gtts import gTTS

HERE = Path(__file__).resolve().parent
OUT = HERE / 'out'
FIRST_START = 0.6   # seconds of silence before the first line
GAP = 0.45          # pause between lines
TEMPO = 1.25        # speed-up applied to every line
DURATION = 30.0


def run(*args: str) -> str:
    return subprocess.run(args, check=True, capture_output=True, text=True).stdout.strip()


def duration(path: Path) -> float:
    return float(run('ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', str(path)))


def main() -> None:
    OUT.mkdir(exist_ok=True)
    lines = [line.strip() for line in (HERE / 'narration.txt').read_text(encoding='utf-8').splitlines() if line.strip()]
    timeline, inputs, delays = [], [], []
    start = FIRST_START
    for index, text in enumerate(lines, 1):
        raw = OUT / f'narration-raw-{index}.mp3'
        clip = OUT / f'narration-{index}.wav'
        gTTS(text, lang='zh-TW').save(str(raw))
        run('ffmpeg', '-v', 'error', '-y', '-i', str(raw), '-af',
            'silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.02,'
            'areverse,silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.05,'
            f'areverse,atempo={TEMPO}', '-ar', '48000', '-ac', '1', str(clip))
        length = duration(clip)
        timeline.append({'text': text, 'start': round(start, 3), 'end': round(start + length, 3)})
        inputs += ['-i', str(clip)]
        delays.append(f'[{index - 1}]adelay={int(start * 1000)}|{int(start * 1000)}[a{index}]')
        start += length + GAP
    if timeline[-1]['end'] > DURATION - 1.0:
        raise SystemExit(f"Narration ends at {timeline[-1]['end']:.2f}s; shorten the text to leave a closing beat.")
    mix = ';'.join(delays) + ';' + ''.join(f'[a{i}]' for i in range(1, len(lines) + 1)) + \
        f'amix=inputs={len(lines)}:normalize=0,apad,atrim=0:{DURATION},loudnorm=I=-16:TP=-1.5:LRA=11[out]'
    run('ffmpeg', '-v', 'error', '-y', *inputs, '-filter_complex', mix, '-map', '[out]', '-ar', '48000', '-ac', '1',
        str(OUT / 'narration.wav'))
    (OUT / 'narration.json').write_text(json.dumps({'lines': timeline}, ensure_ascii=False, indent=1), encoding='utf-8')
    for item in timeline:
        print(f"{item['start']:6.2f}–{item['end']:6.2f}  {item['text']}")


if __name__ == '__main__':
    main()
