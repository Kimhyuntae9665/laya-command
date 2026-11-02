"""Download pinned model artifacts and the Windows CPU llama.cpp release."""
import argparse
import hashlib
import json
from pathlib import Path
import urllib.request
import zipfile

QWEN_REPO = 'unsloth/Qwen3-4B-Instruct-2507-GGUF'
QWEN_REVISION = 'a06e946bb6b655725eafa393f4a9745d460374c9'
QWEN_FILE = 'Qwen3-4B-Instruct-2507-Q4_K_M.gguf'
QWEN_SHA256 = '3605803b982cb64aead44f6c1b2ae36e3acdb41d8e46c8a94c6533bc4c67e597'
LAYA_REVISION = '7b928d828b7b0e022f929d9bd2e44165aa270148'
LLAMA_URL = 'https://github.com/ggml-org/llama.cpp/releases/download/b11960/llama-b11960-bin-win-cpu-x64.zip'


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(8 * 1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def check(runtime):
    required = ['llama-cpp/llama-server.exe', 'models/' + QWEN_FILE,
                'models/laya-english/model.safetensors',
                'models/laya-english/encoder/config.json',
                'models/laya-english/tokenizer/tokenizer.json',
                'models/laya-english/rl_agent_config.json']
    missing = [name for name in required if not (runtime / name).is_file()]
    if missing:
        raise RuntimeError('Missing runtime files: ' + ', '.join(missing))
    if digest(runtime / 'models' / QWEN_FILE) != QWEN_SHA256:
        raise RuntimeError('Qwen GGUF SHA-256 mismatch.')
    import laya
    import torch
    print(json.dumps({'status': 'ready', 'qwen_sha256': QWEN_SHA256,
                      'laya': laya.__version__, 'torch': torch.__version__}, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runtime', type=Path, required=True)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    runtime = args.runtime.resolve()
    if args.check:
        check(runtime)
        return
    from huggingface_hub import hf_hub_download, snapshot_download
    models = runtime / 'models'
    models.mkdir(parents=True, exist_ok=True)
    hf_hub_download(QWEN_REPO, QWEN_FILE, revision=QWEN_REVISION, local_dir=models)
    if digest(models / QWEN_FILE) != QWEN_SHA256:
        raise RuntimeError('Qwen GGUF SHA-256 mismatch.')
    snapshot_download('convaiinnovations/laya', revision=LAYA_REVISION,
                      local_dir=models / 'laya-english',
                      allow_patterns=['model.safetensors', 'config.json', 'rl_agent_config.json',
                                      'encoder/*', 'tokenizer/*'])
    archive = runtime / 'llama-cpu-b11960.zip'
    urllib.request.urlretrieve(LLAMA_URL, archive)
    destination = runtime / 'llama-cpp'
    destination.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive) as z:
        for entry in z.infolist():
            target = (destination / entry.filename).resolve()
            if not target.is_relative_to(destination.resolve()):
                raise RuntimeError('Unsafe archive member.')
        z.extractall(destination)
    check(runtime)


if __name__ == '__main__':
    main()
