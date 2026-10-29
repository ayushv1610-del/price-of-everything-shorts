# Character dialogue checkpoint

This is a tested local production path, not a completed autonomous channel.

`kokoro_voice.py` synthesizes three distinct stock neural voices locally, without a paid speech API. It requires the upstream Kokoro ONNX model and voices files in `SHORTS_VOICE_MODEL_DIR`. `dialogue.py` validates PCM audio, detects silence and clipping, rejects missing dialogue and the old flite provider, and builds a dialogue timeline. Audio checks are technical checks; they do not establish voice acting quality or transcript accuracy.

Reproduce the current cartoon:

```
python -m pip install -r requirements-voice.txt
SHORTS_VOICE_MODEL_DIR=/path/to/voice-models python cartoon_pilot.py
python -m unittest -v test_dialogue test_production test_system
```

Download the model assets from the upstream project's documented model-files-v1.1 release:
https://github.com/thewh1teagle/kokoro-onnx

Model filenames: `kokoro-v1.0.onnx`, `voices-v1.0.bin`. Do not commit model binaries or credentials. Upstream runtime is MIT; model weights are Apache 2.0. Preserve their respective notices when packaging.

Verified local output: 720x1280, 30fps, 18.476 seconds, H.264/AAC; complete decode passed. The cartoon renderer measures the speech signal each frame to drive mouth opening. Timing is audio-reactive, not phoneme-level lip sync. Original code-drawn animation remains basic. The user-approved neural-voice pilot was later published as ITYm5XS6zGs. See README for the subsequent cloud automation implementation and verify deployment status independently.

Remaining: provision model assets in the separate Shorts runtime, connect voice validation to the deployed queue and publishing gate, add story diversity and performance retrieval, and verify the whole deployed workflow. Existing demo publishing exclusions remain in place. The already published silent test is fv31OtDTlq0. JARVIS is outside scope.
