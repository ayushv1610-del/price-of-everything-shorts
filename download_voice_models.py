"""Download release-pinned models and verify exact checksums at image build time."""
import urllib.request,hashlib,time,os
from pathlib import Path
root=Path(os.environ.get('SHORTS_VOICE_MODEL_DIR','/opt/voice-models'));root.mkdir(parents=True,exist_ok=True)
checks={'kokoro-v1.0.onnx':'beb0d1848dee9a49da392cc3df26958d46cfa35d321edf434f52949153f0df3a',
        'voices-v1.0.bin':'bca610b8308e8d99f32e6fe4197e7ec01679264efed0cac9140fe9c29f1fbf7d'}
for name,digest in checks.items():
    path=root/name
    for attempt in range(3):
        try:
            urllib.request.urlretrieve('https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.1/'+name,path)
            if hashlib.sha256(path.read_bytes()).hexdigest()!=digest:raise ValueError('Model checksum mismatch')
            break
        except Exception:
            if attempt==2:raise
            time.sleep(2)
(root/'MODEL_LICENSE.txt').write_text('Kokoro model: Apache License 2.0. https://huggingface.co/hexgrad/Kokoro-82M\nRuntime: kokoro-onnx, MIT. https://github.com/thewh1teagle/kokoro-onnx\n')
urllib.request.urlretrieve('https://www.apache.org/licenses/LICENSE-2.0.txt',root/'Apache-2.0.txt')
