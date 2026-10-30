# Packs the voice style files from the kokoro-js npm package into kokoro_voices.npz for kokoro-onnx.
# Usage: npm pack kokoro-js && tar -xzf kokoro-js-*.tgz && python3 build_voices.py package/voices
import glob, os, sys
import numpy as np
SRC = sys.argv[1]
voices = {os.path.basename(f)[:-4]: np.fromfile(f, dtype=np.float32).reshape(510, 1, 256) for f in sorted(glob.glob(os.path.join(SRC, '*.bin')))}
np.savez(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'kokoro_voices.npz'), **voices)
print(len(voices), 'voices')
