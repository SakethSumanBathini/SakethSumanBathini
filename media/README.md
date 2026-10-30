# Demo video sources

How `leak-trace-demo.mp4` is made, end to end. Everything runs offline.

1. `voice/make_voice.py` speaks each line of `voice/narration.json` with the SVOX Pico voice (`pico2wave`, en-US), then cleans and brightens it with ffmpeg.
2. `video/record_vo.py <index.html> 4` drives the live page in headless Chromium at 1080p (seed 4 for the leaks), waits for each voice line, captures frames over the DevTools screencast and logs when every sound should play. Scrolls are stepped one frame at a time so they stay smooth.
3. `video/compose_audio.py` places the voice, writes an original music bed in D major (pad, electric piano, bass and light drums, all synthesised in NumPy), adds the interface sounds, ducks the music under the voice and normalises the mix to -16 LUFS. It also writes the subtitles.
4. `video/make_video.py leak-trace-demo.mp4` turns the frames into a 30 fps H.264 video on the recorded timeline and adds the soundtrack.

Needs: Python 3 with Playwright, NumPy, SciPy, soundfile and pyloudnorm; ffmpeg; `libttspico-utils`.
