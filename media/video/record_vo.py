# Records the narrated walkthrough of the Leak Trace demo at 1080p.
# Each scene waits for its voice line, and every sound cue is logged with its time.
# Usage: python3 record_vo.py <bundle.html> <seed>
import asyncio, base64, json, os, shutil, sys, time
from playwright.async_api import async_playwright

SRC, SEED = sys.argv[1], int(sys.argv[2])
HERE = os.path.dirname(os.path.abspath(__file__))
VOICE = os.path.join(os.path.dirname(HERE), 'voice')
CAPDIR = os.path.join(HERE, 'cap')
DUR = json.load(open(os.path.join(VOICE, 'durations.json')))

INIT = """
(function(){ var a = %d; Math.random = function(){ a |= 0; a = (a + 0x6D2B79F5) | 0; var t = Math.imul(a ^ (a >>> 15), 1 | a); t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t; return ((t ^ (t >>> 14)) >>> 0) / 4294967296; }; })();
""" % SEED
CAP_CSS = """
#cap { position: fixed; left: 50%; bottom: 28px; transform: translateX(-50%); z-index: 99; max-width: 1040px; padding: 14px 24px 15px;
  background: rgba(19, 30, 138, 0.94); color: #fff; font: 700 25px/1.25 'Bricolage Grotesque', system-ui, sans-serif; font-stretch: 85%;
  border-radius: 6px; box-shadow: 0 6px 24px rgba(0,0,0,0.18); opacity: 0; transition: opacity 0.35s; text-align: center; }
#cap.on { opacity: 1; }
#cap small { display: block; font: 500 16px/1.3 'Bricolage Grotesque', system-ui, sans-serif; opacity: 0.85; margin-top: 4px; }
.top { display: none !important; }
#endcard { position: fixed; inset: 0; z-index: 100; background: #fff; display: none; flex-direction: column; justify-content: center; padding: 0 110px; font-family: 'Bricolage Grotesque', system-ui, sans-serif; opacity: 0; transition: opacity 0.6s; }
#endcard.on { opacity: 1; }
#endcard h1 { font-size: 92px; line-height: 0.9; color: #1E2FC6; margin: 0 0 22px; }
#endcard p { font-size: 26px; margin: 6px 0; color: #151938; }
#endcard .s { font-size: 19px; color: #5A5E76; }
"""
ENDCARD = ("<h1>Leak Trace</h1><p>Tracing a leaked exam paper to the college that printed it.</p>"
           "<p class=s>Seva First Innovation Challenge 2026 · South Zone · Theme 4 · Track A</p>"
           "<p class=s>Team from Sreyas Institute of Engineering and Technology, Hyderabad</p>"
           "<p class=s>Live demo, research paper and code: links in the description</p>")

async def main():
    shutil.rmtree(CAPDIR, ignore_errors=True); os.makedirs(CAPDIR)
    frames, events, log = [], [], []
    FPS = 30
    clock = {'t0': None, 'vo_end': 0.0, 'n': 0, 'stop': False, 'offset': 0.0, 'stepping': False, 'step_vt': 0.0, 'want_y': None}
    got = asyncio.Event()
    # Video time runs with the wall clock, except during stepped scrolls, where each step is one frame
    now = lambda: time.monotonic() - clock['t0'] - clock['offset']
    def ev(kind, at=None, **kw):
        events.append(dict(kind=kind, t=round(now() if at is None else at, 3), **kw))
    async with async_playwright() as p:
        b = await p.chromium.launch(args=['--force-device-scale-factor=1.5'])
        ctx = await b.new_context(viewport={'width': 1280, 'height': 720}, device_scale_factor=1.5)
        await ctx.add_init_script(INIT)
        pg = await ctx.new_page()
        await pg.goto('file://' + SRC, wait_until='load')
        await pg.add_style_tag(content=CAP_CSS)
        await pg.evaluate("(h) => { const e = document.createElement('div'); e.id = 'endcard'; e.innerHTML = h; document.body.appendChild(e); }", ENDCARD)
        await pg.evaluate("() => document.fonts.ready")
        await pg.wait_for_timeout(800)

        cdp = await ctx.new_cdp_session(pg)
        async def on_frame(prm):
            i = clock['n']; clock['n'] += 1
            y = prm['metadata'].get('scrollOffsetY', 0)
            if clock['t0'] is None: t = -1.0
            elif clock['stepping']: t = clock['step_vt']
            else: t = now()
            path = os.path.join(CAPDIR, f'f{i:05d}.jpg')
            with open(path, 'wb') as fh: fh.write(base64.b64decode(prm['data']))
            frames.append((t, path))
            if clock['want_y'] is not None and abs(y - clock['want_y']) < 1.5: got.set()
            if not clock['stop']:
                try: await cdp.send('Page.screencastFrameAck', {'sessionId': prm['sessionId']})
                except Exception: pass
        cdp.on('Page.screencastFrame', lambda prm: asyncio.ensure_future(on_frame(prm)))
        await cdp.send('Page.startScreencast', {'format': 'jpeg', 'quality': 88, 'maxWidth': 1920, 'maxHeight': 1080})
        await pg.wait_for_timeout(600)

        async def cap(text, sub=''):
            await pg.evaluate("""([t, s]) => { let c = document.getElementById('cap'); if (!c) { c = document.createElement('div'); c.id = 'cap'; document.body.appendChild(c); }
              c.classList.remove('on'); setTimeout(() => { c.innerHTML = ''; c.appendChild(document.createTextNode(t)); if (s) { const sm = document.createElement('small'); sm.textContent = s; c.appendChild(sm); } c.classList.add('on'); }, 250); }""", [text, sub])
        async def nocap():
            await pg.evaluate("() => { const c = document.getElementById('cap'); if (c) c.classList.remove('on'); }")
        async def scroll_to(sel, offset=-40, dur=900):
            # Stepped scroll: one position per video frame, each held until the browser has drawn it
            if dur >= 900: ev('whoosh', dur=dur / 1000)
            y0, y1 = await pg.evaluate("""([sel, off]) => { const el = document.querySelector(sel); const max = document.scrollingElement.scrollHeight - innerHeight;
              return [scrollY, Math.max(0, Math.min(max, el.getBoundingClientRect().top + scrollY + off))]; }""", [sel, offset])
            n = max(2, round(dur / 1000 * FPS)); vt0 = now(); r0 = time.monotonic()
            clock['stepping'] = True
            for i in range(1, n + 1):
                a = i / n; e = 2*a*a if a < 0.5 else 1 - (-2*a + 2) ** 2 / 2
                clock['step_vt'] = vt0 + i / FPS; got.clear()
                clock['want_y'] = await pg.evaluate("(y) => { window.scrollTo(0, y); return window.scrollY; }", y0 + (y1 - y0) * e)
                try: await asyncio.wait_for(got.wait(), 0.6)
                except asyncio.TimeoutError: pass
            clock['stepping'] = False; clock['want_y'] = None
            clock['offset'] += (time.monotonic() - r0) - n / FPS
        async def status(ak=False):
            s = (await pg.inner_text('#akStatus' if ak else '#status')).strip()
            w = (await pg.inner_text('#akWho' if ak else '#who')).strip()
            r = (await pg.inner_text('#akReveal' if ak else '#reveal')).strip()
            log.append((s, w, r)); return s.lower()
        async def say(vid, gap=0.15):
            t = now()
            if t < clock['vo_end'] + gap: await asyncio.sleep(clock['vo_end'] + gap - t)
            ev('vo', id=vid, dur=DUR[vid]); clock['vo_end'] = now() + DUR[vid]
        async def wait_vo(pad=0.5):
            t = now()
            if t < clock['vo_end'] + pad: await asyncio.sleep(clock['vo_end'] + pad - t)
        async def check(sel):
            ev('click'); await pg.check(sel); return now()
        sleep = asyncio.sleep

        # ---- start of the video
        clock['t0'] = time.monotonic()
        await pg.evaluate("() => document.getElementById('replay').click()")
        ev('start')
        # 1 hero
        await cap('A university paper leaks on WhatsApp at 9:04.', 'Which of 500 colleges leaked it?')
        await sleep(0.4); await say('hero'); await wait_vo(0.6)
        # 2 one paper, many patterns
        await scroll_to('#trick', -10, 1200)
        await cap('Every college gets the same questions and marks…', '…in its own order, with its own approved wording.')
        await say('trick'); await sleep(2.2); await scroll_to('#papers', -20, 800)
        ev('tick'); await pg.hover('#papers li[data-q="4"]'); await sleep(2.4)
        ev('tick'); await pg.hover('#papers li[data-q="8"]'); await wait_vo(0.5)
        # 3 layers
        await scroll_to('#layersTitle', -30, 1000)
        await cap('Three layers of marks.', 'Change the numbers or answers, and the leaked answers turn wrong.')
        await say('layers'); await wait_vo(0.6)
        # 4 be the leaker
        await scroll_to('#demo .bench', -60, 1000)
        await cap('Be the leaker: retype seven questions, with typos, no numbers.')
        await say('demo'); await sleep(2.2)
        await check('input[name=num][value=none]'); await sleep(1.0)
        tk = await check('input[name=k][value="7"]'); await sleep(0.4)
        st1 = await status()
        if 'named' not in st1: raise SystemExit('scene 4: expected a named source, got ' + st1)
        ev('named', at=tk + 0.2)
        await wait_vo(0.4)
        await cap('Leak Trace names the college only at 10,000 to 1…', '…and here it does.')
        await say('named'); await wait_vo(0.5)
        await scroll_to('#demo .meter-fig', -40, 1000)
        await cap('The odds grow line by line until one college crosses the bar.')
        await say('meter'); await wait_vo(1.4)
        # 5 dodge
        await scroll_to('#demo .bench', -60, 1000)
        await cap('Now try to dodge it: reword and shuffle everything.')
        await say('dodge'); await sleep(1.9)
        await check('#optReword'); await sleep(0.9)
        tk = await check('#optShuffle'); await sleep(0.4)
        st2 = await status()
        if 'held' not in st2: raise SystemExit('scene 5: expected held back, got ' + st2)
        ev('held', at=tk + 0.2)
        await wait_vo(0.4)
        await cap('It holds back instead of guessing.', 'Order and wording are gone, so no one is named. Numbers and answers survive.')
        await say('held'); await wait_vo(0.6)
        await nocap()
        # 6 answer keys
        await scroll_to('#keys', -10, 1200)
        await pg.evaluate("() => { for (const id of ['optReword', 'optShuffle']) { const x = document.getElementById(id); x.checked = false; } }")
        await cap('Even a leaked answer key gives the college away.', 'With coded keys, any two colleges differ in at least 12 of 20 answers.')
        await say('keys'); await sleep(4.6)
        await scroll_to('#keys .bench', -60, 1000)
        await wait_vo(0.2)
        tk = await check('input[name=ae][value="0.1"]'); await sleep(0.4)
        st3 = await status(ak=True)
        if 'named' not in st3: raise SystemExit('scene 6: expected the key to be named, got ' + st3)
        ev('named', at=tk + 0.2)
        await sleep(0.5)
        await cap('16 answers, one wrong in ten:', 'named, with the leaked bubbles matched to that college’s key.')
        await say('keynamed'); await wait_vo(0.4)
        await scroll_to('#keys .meter-fig', -40, 1000); await sleep(2.6)
        # 7 batch
        await scroll_to('#demo .batch', -40, 1200)
        await cap('Run 200 random leaks at once.')
        await say('batch'); await sleep(0.9)
        ev('click'); ev('batch_start'); await pg.click('#batchBtn')
        await pg.wait_for_selector('#stats:not([hidden])', timeout=30000)
        ev('batch_end')
        sn = (await pg.inner_text('#sWrong')).strip(); log.append(('batch wrong', sn, ''))
        if sn != '0': raise SystemExit('scene 7: expected 0 innocent colleges, got ' + sn)
        await wait_vo(0.5)
        await cap('Innocent colleges blamed: ' + sn + '.', 'Across 148,000 attack leaks: 1, a chance match on an outside copy.')
        await say('zero'); await wait_vo(0.6)
        # 8 guarantee
        await scroll_to('#guarantee', -20, 1200)
        await cap('Proven, under our model: an outside copy clears the bar at most 1 in 10,000 times.', 'Checked on 800,000 simulated copies; no real leak pinned on the wrong college.')
        await say('proof'); await wait_vo(0.8)
        # 9 research
        await scroll_to('#research', -20, 1200)
        await cap('A 15-page research paper, open code and data.', 'All results so far are simulated; a pilot is next.')
        await say('paper'); await wait_vo(0.7)
        # 10 end card
        await nocap()
        await pg.evaluate("() => { const e = document.getElementById('endcard'); e.style.display = 'flex'; requestAnimationFrame(() => requestAnimationFrame(() => e.classList.add('on'))); }")
        ev('end'); await sleep(0.5)
        await say('end'); await wait_vo(3.2)
        t_end = now()
        clock['stop'] = True
        await cdp.send('Page.stopScreencast'); await pg.wait_for_timeout(300)
        await b.close()
    fr = [(round(t, 4), path) for t, path in frames]
    json.dump({'seed': SEED, 't_end': round(t_end, 3), 'frames': fr, 'events': events, 'log': log}, open(os.path.join(HERE, 'timeline.json'), 'w'), indent=0)
    print('seed', SEED, 'end', round(t_end, 2), 's, frames', len(fr), 'before start', sum(1 for t, _ in fr if t < 0))
    print(log)

asyncio.run(main())
