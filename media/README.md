# Demo video sources

How `leak-trace-demo.mp4` is made, end to end. Everything runs offline.

1. `voice/make_voice_kokoro.py <model_quantized.onnx>` speaks each line of `voice/narration.json` with the open-source Kokoro-82M voice model (Apache-2.0; voice "Heart"), using `kokoro-onnx` and the voice files that ship with the `kokoro-js` npm package (`voice/build_voices.py` packs them into `voice/kokoro_voices.npz`). The model file is `onnx/model_quantized.onnx` from onnx-community/Kokoro-82M-v1.0-ONNX on Hugging Face. `voice/make_voice.py` is an older fallback that uses the SVOX Pico voice (`pico2wave`).
2. `video/record_vo.py <index.html> 4` drives the live page in headless Chromium at 1080p (seed 4 for the leaks), waits for each voice line, captures frames over the DevTools screencast and logs when every sound should play. Scrolls are stepped one frame at a time so they stay smooth.
3. `video/compose_audio.py` places the voice, writes an original music bed in D major (pad, electric piano, bass and light drums, all synthesised in NumPy), adds the interface sounds, ducks the music under the voice and normalises the mix to -16 LUFS. It also writes the subtitles.
4. `video/make_video.py leak-trace-demo.mp4` turns the frames into a 30 fps H.264 video on the recorded timeline and adds the soundtrack.

Needs: Python 3 with Playwright, NumPy, SciPy, soundfile, pyloudnorm and kokoro-onnx; ffmpeg; `libttspico-utils` only for the fallback voice.
