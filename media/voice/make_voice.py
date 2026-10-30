# Synthesises each narration line offline (SVOX Pico), then cleans and brightens it. Usage: python3 make_voice.py [lang]
import json, subprocess, sys, os
LANG = sys.argv[1] if len(sys.argv) > 1 else 'en-US'
HERE = os.path.dirname(os.path.abspath(__file__))
lines = json.load(open(os.path.join(HERE, 'narration.json')))
CHAIN = ','.join([
    'aresample=48000:resampler=soxr:precision=28',
    'highpass=f=85',
    'equalizer=f=200:t=q:w=1.0:g=1.0',
    'equalizer=f=2500:t=q:w=1.5:g=1.5',
    'aexciter=amount=0.7:drive=5:blend=0:freq=5600:ceil=16000',
    'acompressor=threshold=-21dB:ratio=2.0:attack=8:release=100:makeup=1',
    'silenceremove=start_periods=1:start_threshold=-48dB',
    'areverse', 'silenceremove=start_periods=1:start_threshold=-48dB', 'areverse',
])
out = {}
for ln in lines:
    raw = os.path.join(HERE, f"raw_{ln['id']}.wav"); wav = os.path.join(HERE, f"vo_{ln['id']}.wav")
    ssml = '<speed level="97">' + ln['text'] + '</speed>'
    subprocess.run(['pico2wave', '-l', LANG, '-w', raw, ssml], check=True)
    subprocess.run(['ffmpeg', '-y', '-v', 'error', '-i', raw, '-af', CHAIN, '-ac', '1', '-c:a', 'pcm_s24le', wav], check=True)
    d = float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', wav], capture_output=True, text=True).stdout)
    out[ln['id']] = round(d, 3)
    print(f"{ln['id']:9s} {d:5.2f}s  {len(ln['text'].split()):3d} words")
json.dump(out, open(os.path.join(HERE, 'durations.json'), 'w'), indent=1)
print('total speech', round(sum(out.values()), 1), 's')
