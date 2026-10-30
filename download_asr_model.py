"""Build-time multilingual ASR download, runtime stays offline."""
import os
from huggingface_hub import snapshot_download
snapshot_download('Systran/faster-whisper-small',
    revision='536b0662742c02347bc0e980a01041f333bce120',
    local_dir=os.environ.get('SHORTS_ASR_MODEL_DIR','/opt/asr-model'),
    allow_patterns=['config.json','model.bin','tokenizer.json','vocabulary.txt','preprocessor_config.json'])
