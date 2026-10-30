# Builds the soundtrack for the narrated walkthrough: voice-over, an original music bed and UI sounds,
# placed from the recorder's timeline, then mixed with ducking and loudness normalisation.
# Usage: python3 compose_audio.py  (reads timeline.json and ../voice, writes mix.wav and leak-trace-demo.srt)
import json, os, re, subprocess
import numpy as np
import soundfile as sf
import pyloudnorm as pyln
from scipy import signal
from scipy.ndimage import maximum_filter1d

HERE = os.path.dirname(os.path.abspath(__file__))
VOICE = os.path.join(os.path.dirname(HERE), 'voice')
SR = 48000
rng = np.random.default_rng(7)
TL = json.load(open(os.path.join(HERE, 'timeline.json')))
EV = TL['events']
T_END = TL['t_end']
N = int((T_END + 0.05) * SR)
TEXT = {l['id']: l.get('sub', l['text']) for l in json.load(open(os.path.join(VOICE, 'narration.json')))}  # subtitles use digits

def hz(m): return 440.0 * 2 ** ((m - 69) / 12)
def at(t): return int(round(t * SR))
def ev_times(kind): return [e for e in EV if e['kind'] == kind]
def place(buf, x, t, gain=1.0):
    i = at(t)
    if i >= len(buf): return
    x = x[: len(buf) - i]
    buf[i:i + len(x)] += gain * x
def pan(x, p):  # p in [-1, 1], constant power
    a = (p + 1) * np.pi / 4
    return np.stack([x * np.cos(a), x * np.sin(a)], axis=1)
def lp(x, f, order=2): return signal.sosfilt(signal.butter(order, f, 'low', fs=SR, output='sos'), x, axis=0)
def hp(x, f, order=2): return signal.sosfilt(signal.butter(order, f, 'high', fs=SR, output='sos'), x, axis=0)
def bp(x, lo, hi, order=2): return signal.sosfilt(signal.butter(order, [lo, hi], 'band', fs=SR, output='sos'), x, axis=0)

def reverb_ir(rt60, length, predelay=0.02, hp_f=250, lp_f=6500):
    n = int(length * SR); t = np.arange(n) / SR
    ir = rng.standard_normal((n, 2)) * np.exp(-6.91 * t / rt60)[:, None]
    ir = lp(hp(ir, hp_f), lp_f)
    ir = np.concatenate([np.zeros((int(predelay * SR), 2)), ir])
    return ir / np.sqrt((ir ** 2).sum(axis=0, keepdims=True))
def convolve_st(x, ir):
    return np.stack([signal.fftconvolve(x[:, c], ir[:, c])[: len(x)] for c in range(2)], axis=1)

# ------------------------------------------------------------------ voice-over
vo = np.zeros(N)
spans = []
for e in ev_times('vo'):
    x, sr = sf.read(os.path.join(VOICE, f"vo_{e['id']}.wav"))
    assert sr == SR
    place(vo, x, e['t']); spans.append((e['t'], e['t'] + len(x) / SR, e['id']))
meter = pyln.Meter(SR)
vo *= 10 ** ((-16.0 - meter.integrated_loudness(vo)) / 20)
vo_st = np.stack([vo, vo], axis=1)
vo_st = vo_st + 0.05 * convolve_st(vo_st, reverb_ir(0.3, 0.5, predelay=0.008, hp_f=400, lp_f=4500))

# ------------------------------------------------------------------ music bed (original, D major, 96 bpm)
BPM = 96; BEAT = 60 / BPM; BAR = 4 * BEAT
t_end_card = ev_times('end')[0]['t']
t_a = next(e['t'] for e in EV if e['kind'] == 'vo' and e['id'] == 'trick')
t_b = next(e['t'] for e in EV if e['kind'] == 'vo' and e['id'] == 'demo')
PROG = [  # (bass, pad voicing, arpeggio tones)
    (38, [57, 62, 66, 69], [62, 66, 69, 74]),   # D
    (35, [54, 59, 62, 66], [59, 62, 66, 71]),   # Bm
    (31, [55, 59, 62, 67], [59, 62, 67, 71]),   # G
    (33, [57, 61, 64, 69], [57, 61, 64, 69]),   # A
]
pad = np.zeros((N, 2)); arp = np.zeros((N, 2)); bass = np.zeros(N); drums = np.zeros((N, 2))

def saw(f, n, ph0=0.0):  # PolyBLEP sawtooth
    dt = f / SR; ph = (ph0 + dt * np.arange(n)) % 1.0
    y = 2 * ph - 1
    m = ph < dt; x = ph[m] / dt; y[m] -= x + x - x * x - 1
    m = ph > 1 - dt; x = (ph[m] - 1) / dt; y[m] -= x * x + x + x + 1
    return y
def env_ar(n, a, r_start, r):
    t = np.arange(n) / SR
    e = np.minimum(1, t / a) ** 2
    rel = np.clip((t - r_start) / r, 0, 1)
    return e * (1 - rel) ** 2
def pad_chord(notes, t0, length, gain=0.05, attack=0.6, release=1.0):
    n = at(length + release)
    env = env_ar(n, attack, length, release)
    for m in notes:
        for det, p in ((-0.09, -0.6), (0.0, 0.0), (0.09, 0.6)):
            x = saw(hz(m + det), n, rng.random()) * env * gain
            place(pad, pan(x, p), t0)
def epiano(f, dur=1.1, vel=1.0):
    n = at(dur); t = np.arange(n) / SR
    idx = 1.6 * np.exp(-t / 0.22) + 0.25
    y = np.sin(2 * np.pi * f * t + idx * np.sin(2 * np.pi * f * t)) + 0.18 * np.sin(4 * np.pi * f * t) * np.exp(-t / 0.15)
    e = (1 - np.exp(-t / 0.004)) * np.exp(-t / 0.55)
    return vel * y * e
def kick():
    n = at(0.45); t = np.arange(n) / SR
    f = 46 + 68 * np.exp(-t / 0.035)
    y = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.2)
    y[: at(0.003)] += hp(rng.standard_normal(at(0.003)), 2000) * 0.3
    return y
def hat(vel=1.0):
    n = at(0.09); t = np.arange(n) / SR
    return vel * hp(rng.standard_normal(n), 7500, 4) * np.exp(-t / 0.028)
def rim(vel=1.0):
    n = at(0.14); t = np.arange(n) / SR
    return vel * (bp(rng.standard_normal(n), 1400, 3200) * np.exp(-t / 0.045) + 0.4 * np.sin(2 * np.pi * 330 * t) * np.exp(-t / 0.03))

kick_times = []
bar = 0
while bar * BAR < t_end_card:
    t0 = bar * BAR
    b_note, voicing, tones = PROG[bar % 4]
    length = min(BAR, t_end_card - t0)
    pad_chord(voicing, t0, length)
    # arpeggio: eighth notes, pattern over the chord tones, softer in the intro
    pat = [0, 1, 2, 3, 2, 1, 2, 1]
    for k, ix in enumerate(pat):
        tt = t0 + k * BEAT / 2
        if tt >= t_end_card: break
        vel = (0.55 if k % 2 == 0 else 0.4) * (0.55 if tt < t_a else 1.0)
        x = epiano(hz(tones[ix] + 12 if k == 3 else tones[ix]), vel=vel)
        place(arp, pan(x, -0.35 if k % 2 == 0 else 0.35), tt)
    if t0 >= t_a - 0.01:
        for beat in range(4):
            tt = t0 + beat * BEAT
            if tt >= t_end_card: break
            if beat in (0, 2):
                place(drums, pan(kick(), 0.0), tt, 0.55); kick_times.append(tt)
                n = at(min(BEAT * 2, t_end_card - tt)); tb = np.arange(n) / SR
                f = hz(b_note + 12)
                y = (np.sin(2 * np.pi * f * tb) + 0.25 * np.sin(4 * np.pi * f * tb) + 0.08 * np.sin(6 * np.pi * f * tb))
                y *= np.minimum(1, tb / 0.015) * np.exp(-tb / 1.6) * (1.0 if beat == 0 else 0.8)
                y[-at(0.03):] *= np.linspace(1, 0, at(0.03))
                place(bass, y, tt, 0.20)
            if t0 >= t_b - 0.01 and beat in (1, 3):
                place(drums, pan(rim(), 0.1), tt, 0.10)
        if t0 >= t_b - 0.01:
            for k in range(8):
                tt = t0 + k * BEAT / 2 + BEAT / 4
                if tt < t_end_card: place(drums, pan(hat(0.8 if k % 2 else 0.55), 0.3), tt, 0.07)
    bar += 1

# ending: the final D major chord with the end card, then a slow fade
t_f = t_end_card
pad_chord([50, 57, 62, 66, 69], t_f, max(0.5, T_END - t_f - 1.4), gain=0.05, attack=0.35, release=1.4)
tail = T_END - t_f
nb = at(tail); tb = np.arange(nb) / SR
y = np.sin(2 * np.pi * hz(38 + 12) * tb) * np.minimum(1, tb / 0.02) * np.exp(-tb / 2.5)
place(bass, y, t_f, 0.22)
for k, m in enumerate([74, 69, 66, 62, 69, 74, 78, 86]):
    place(arp, pan(epiano(hz(m), dur=2.0, vel=0.42 - 0.02 * k), -0.3 + 0.08 * k), t_f + 0.15 + k * BEAT / 2)

# sidechain pump from the kick on pad and bass (subtle)
pump = np.ones(N)
for tt in kick_times:
    i = at(tt); n = min(at(0.32), N - i); x = np.arange(n) / SR
    pump[i:i + n] = np.minimum(pump[i:i + n], 1 - 0.28 * np.exp(-x / 0.12))
pad *= pump[:, None]; bass *= pump

pad = lp(pad, 1700); arp = lp(arp, 5200); bass = lp(bass, 420)
music = pad + arp + pan(bass, 0) + drums
music[: at(2.5)] *= np.linspace(0, 1, at(2.5))[:, None] ** 1.5
music = music + 0.24 * convolve_st(lp(hp(music, 200), 7000), reverb_ir(2.2, 3.0, predelay=0.025))
fade = at(2.2); music[-fade:] *= np.linspace(1, 0, fade)[:, None] ** 2
music *= 10 ** ((-22.0 - meter.integrated_loudness(music)) / 20)

# ducking under the voice: -10 dB, fast in, slow out (computed at 1 kHz control rate)
CR = 1000; nc = int(T_END * CR) + 2
target = np.zeros(nc)
for a, b, _ in spans: target[max(0, int((a - 0.15) * CR)): int((b + 0.2) * CR)] = 1
act = np.zeros(nc); g = 0.0
up, down = 1 - np.exp(-1 / (0.15 * CR)), 1 - np.exp(-1 / (0.7 * CR))
for i in range(nc):
    g += (target[i] - g) * (up if target[i] > g else down); act[i] = g
# split ducking: the speech band (above 300 Hz) drops 23 dB under the voice, the low end only 11 dB
a_full = np.interp(np.arange(N) / SR, np.arange(nc) / CR, act)
m_low = lp(music, 300, 4); m_high = music - m_low
music = m_low * (10 ** (-11.0 * a_full / 20))[:, None] + m_high * (10 ** (-23.0 * a_full / 20))[:, None]

# ------------------------------------------------------------------ UI sounds
sfx = np.zeros((N, 2))
def click(vel=1.0):
    n = at(0.03); t = np.arange(n) / SR
    y = bp(rng.standard_normal(n), 2500, 7000) * np.exp(-t / 0.0025) * 0.9 + np.sin(2 * np.pi * 1850 * t) * np.exp(-t / 0.006) * 0.5
    return vel * y
def bell(f, dur=1.6, vel=1.0):
    n = at(dur); t = np.arange(n) / SR
    y = (np.sin(2 * np.pi * f * t) * np.exp(-t / 0.7) + 0.35 * np.sin(2 * np.pi * 2.0 * f * t) * np.exp(-t / 0.35)
         + 0.12 * np.sin(2 * np.pi * 3.01 * f * t) * np.exp(-t / 0.18))
    return vel * y * (1 - np.exp(-t / 0.002))
def marimba(f, dur=0.9, vel=1.0):
    n = at(dur); t = np.arange(n) / SR
    y = np.sin(2 * np.pi * f * t) * np.exp(-t / 0.28) + 0.3 * np.sin(2 * np.pi * 3.93 * f * t) * np.exp(-t / 0.05)
    return vel * y * (1 - np.exp(-t / 0.002))
def whoosh(dur):
    n = at(dur + 0.25); t = np.arange(n) / SR; x = rng.standard_normal(n)
    out = np.zeros(n); seg = at(0.02)
    for s0 in range(0, n, seg):
        c = s0 / n; fc = 350 + 2300 * np.sin(np.pi * c) ** 1.5
        out[s0:s0 + seg] = bp(x[max(0, s0 - 2000): s0 + seg], fc * 0.6, fc * 1.6)[-len(out[s0:s0 + seg]):]
    e = np.sin(np.pi * np.clip(t / (dur + 0.25), 0, 1)) ** 2
    return out * e
def peak_to(x, db): return x * (10 ** (db / 20) / (np.abs(x).max() + 1e-12))

for e in EV:
    k, t = e['kind'], e['t']
    if k == 'click': place(sfx, pan(peak_to(click(), -20), 0.05), t)
    elif k == 'tick': place(sfx, pan(peak_to(click(0.6), -28), -0.1), t)
    elif k == 'whoosh':
        w = whoosh(e['dur'])
        place(sfx, np.stack([w * np.linspace(1.0, 0.6, len(w)), w * np.linspace(0.6, 1.0, len(w))], axis=1) * (10 ** (-31 / 20) / (np.abs(w).max() + 1e-12)), t - 0.05)
    elif k == 'named':
        place(sfx, pan(peak_to(bell(hz(81)), -17), -0.15), t)
        place(sfx, pan(peak_to(bell(hz(86)), -17), 0.15), t + 0.12)
    elif k == 'held':
        place(sfx, pan(peak_to(marimba(hz(76)), -22), 0.0), t)
        place(sfx, pan(peak_to(marimba(hz(73)), -22), 0.0), t + 0.16)
    elif k == 'batch_start':
        t_stop = next(x['t'] for x in EV if x['kind'] == 'batch_end')
        tt, i = t, 0
        while tt < t_stop:
            f = 1300 + 1100 * (tt - t) / max(0.3, t_stop - t)
            n = at(0.012); x = np.sin(2 * np.pi * f * np.arange(n) / SR) * np.exp(-np.arange(n) / SR / 0.003)
            place(sfx, pan(x * 10 ** (-33 / 20), 0.5 * np.sin(i)), tt); tt += 0.045; i += 1
    elif k == 'batch_end':
        place(sfx, pan(peak_to(bell(hz(86), vel=0.8), -21), 0.0), t)
    elif k == 'end':
        n = at(2.4); tb = np.arange(n) / SR
        boom = np.sin(2 * np.pi * np.cumsum(55 + 30 * np.exp(-tb / 0.08)) / SR) * np.exp(-tb / 0.9)
        place(sfx, pan(peak_to(boom, -15), 0.0), t + 0.05)
        place(sfx, pan(peak_to(bell(hz(86), dur=2.4), -19), -0.2), t + 0.05)
        place(sfx, pan(peak_to(bell(hz(93), dur=2.4), -22), 0.2), t + 0.11)

# ------------------------------------------------------------------ mix, loudness, limiting
mix = vo_st + music + sfx
gain_db = -16.0 - meter.integrated_loudness(mix)
mix *= 10 ** ((gain_db + 0.3) / 20)
pre = os.path.join(HERE, 'mix_pre.wav'); out = os.path.join(HERE, 'mix.wav')
sf.write(pre, mix.astype(np.float32), SR, subtype='FLOAT')
subprocess.run(['ffmpeg', '-y', '-v', 'error', '-i', pre, '-af',
                'aresample=192000,alimiter=limit=0.82:attack=4:release=60:level=false,aresample=48000',
                '-c:a', 'pcm_s24le', out], check=True)
for name, x in (('voice', vo_st), ('music', music), ('sfx', sfx)):
    sf.write(os.path.join(HERE, f'stem_{name}.wav'), (x * 10 ** ((gain_db + 0.3) / 20)).astype(np.float32), SR, subtype='FLOAT')

# ------------------------------------------------------------------ subtitles from the voice-over timing
def chunks(text, limit=84):
    parts = re.split(r'(?<=[.?!:])\s+', text)
    out = []
    for p in parts:
        while len(p) > limit:
            cut = p.rfind(', ', 0, limit)
            cut = cut + 1 if cut > 20 else p.rfind(' ', 0, limit)
            out.append(p[:cut].strip()); p = p[cut:].strip()
        if p: out.append(p)
    return out
def wrap(s, w=42):
    if len(s) <= w: return s
    mid = len(s) // 2; i = s.rfind(' ', 0, mid + 8)
    return s[:i] + '\n' + s[i + 1:]
def ts(t):
    ms = int(round(t * 1000)); h, ms = divmod(ms, 3600000); m, ms = divmod(ms, 60000); s, ms = divmod(ms, 1000)
    return f'{h:02d}:{m:02d}:{s:02d},{ms:03d}'
cues = []
for a, b, vid in spans:
    cs = chunks(TEXT[vid]); total = sum(len(c) for c in cs); t = a
    for c in cs:
        d = (b - a) * len(c) / total; cues.append((t, t + d, c)); t += d
with open(os.path.join(HERE, 'leak-trace-demo.srt'), 'w') as fh:
    for i, (a, b, c) in enumerate(cues, 1):
        fh.write(f'{i}\n{ts(a)} --> {ts(b)}\n{wrap(c)}\n\n')
print('voice spans', len(spans), '| music LUFS (pre-duck) -22 | mix gain', round(gain_db, 2), 'dB | cues', len(cues))
