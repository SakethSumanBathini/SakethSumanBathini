# Speaks each line of narration.json with the Kokoro-82M voice model (Apache-2.0), fully offline.
# Usage: python3 make_voice_kokoro.py <model.onnx> [voice] [speed]
# Writes vo_<id>.wav (48 kHz) and durations.json, the same outputs as make_voice.py.
import json, os, subprocess, sys
import numpy as np
import soundfile as sf
from kokoro_onnx import Kokoro

MODEL = sys.argv[1]
VOICE = sys.argv[2] if len(sys.argv) > 2 else 'af_heart'
SPEED = float(sys.argv[3]) if len(sys.argv) > 3 else 1.0
HERE = os.path.dirname(os.path.abspath(__file__))
lines = json.load(open(os.path.join(HERE, 'narration.json')))
tts = Kokoro(MODEL, os.path.join(HERE, 'kokoro_voices.npz'))
CHAIN = ','.join([
    'aresample=48000:resampler=soxr:precision=28',
    'highpass=f=70',
    'acompressor=threshold=-20dB:ratio=1.8:attack=10:release=120:makeup=1',
    'silenceremove=start_periods=1:start_threshold=-50dB',
    'areverse', 'silenceremove=start_periods=1:start_threshold=-50dB', 'areverse',
])
lang = 'en-gb' if VOICE[0] == 'b' else 'en-us'
out = {}
for ln in lines:
    audio, sr = tts.create(ln['text'], voice=VOICE, speed=SPEED, lang=lang)
    raw = os.path.join(HERE, f"raw_{ln['id']}.wav"); wav = os.path.join(HERE, f"vo_{ln['id']}.wav")
    sf.write(raw, np.asarray(audio, dtype=np.float32), sr)
    subprocess.run(['ffmpeg', '-y', '-v', 'error', '-i', raw, '-af', CHAIN, '-ac', '1', '-c:a', 'pcm_s24le', wav], check=True)
    os.remove(raw)
    d = float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', wav], capture_output=True, text=True).stdout)
    out[ln['id']] = round(d, 3)
    print(f"{ln['id']:9s} {d:5.2f}s")
json.dump(out, open(os.path.join(HERE, 'durations.json'), 'w'), indent=1)
print('voice', VOICE, '| total speech', round(sum(out.values()), 1), 's')
