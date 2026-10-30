# Turns the captured frames into a 1080p 30 fps video on the recorder's timeline and adds the soundtrack.
# Usage: python3 make_video.py <out.mp4>
import json, os, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = sys.argv[1]
TL = json.load(open(os.path.join(HERE, 'timeline.json')))
t_end = TL['t_end']
frames = TL['frames']
pre = [f for f in frames if f[0] < 0]
post = sorted((f for f in frames if f[0] >= 0), key=lambda f: f[0])
seq = [(0.0, pre[-1][1])] if pre else []
for t, p in post:
    if seq and t - seq[-1][0] < 1e-4: seq[-1] = (seq[-1][0], p)  # several frames for one step: keep the last
    else: seq.append((t, p))
lst = os.path.join(HERE, 'frames.ffconcat')
with open(lst, 'w') as fh:
    fh.write('ffconcat version 1.0\n')
    for i, (t, p) in enumerate(seq):
        nxt = seq[i + 1][0] if i + 1 < len(seq) else t_end
        fh.write(f"file '{p}'\nduration {max(0.001, nxt - t):.4f}\n")
    fh.write(f"file '{seq[-1][1]}'\n")
silent = os.path.join(HERE, 'video_silent.mp4')
subprocess.run(['ffmpeg', '-y', '-v', 'error', '-f', 'concat', '-safe', '0', '-i', lst,
                '-vf', 'fps=30,format=yuv420p', '-c:v', 'libx264', '-preset', 'slow', '-crf', '18',
                '-movflags', '+faststart', '-t', f'{t_end:.3f}', silent], check=True)
subprocess.run(['ffmpeg', '-y', '-v', 'error', '-i', silent, '-i', os.path.join(HERE, 'mix.wav'),
                '-map', '0:v', '-map', '1:a', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-ar', '48000',
                '-metadata', 'title=Leak Trace: demo walkthrough', '-movflags', '+faststart', '-shortest', OUT], check=True)
print('frames used', len(seq), '| duration', t_end)
