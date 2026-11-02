"""Small, disclosed command-routing smoke benchmark; not a general accuracy test."""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import statistics
import time
import warnings

ROOT = Path(__file__).resolve().parents[1]


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('stage', choices=['translate', 'decide'])
    p.add_argument('--runtime', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--reviewed', action='store_true')
    args = p.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    cases = json.loads((ROOT / 'benchmarks/cases.json').read_text(encoding='utf-8'))
    translations_file = args.output / 'translations.json'
    if args.stage == 'translate':
        spec = importlib.util.spec_from_file_location('translator', ROOT / 'skills/ko-en-command/scripts/translate.py')
        translator = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(translator)
        items = []
        for case in cases:
            result = translator.translate(case['source_ko'], runtime=args.runtime)
            items.append({**case, 'translation': result})
            print(json.dumps(items[-1], ensure_ascii=False), flush=True)
            translations_file.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding='utf-8')
        return
    if not args.reviewed:
        p.error('Compare every translation against its Korean source, then pass --reviewed.')
    items = json.loads(translations_file.read_text(encoding='utf-8-sig'))
    if any(x['translation']['warnings'] for x in items):
        raise ValueError('Unresolved translation warning.')
    os.environ.update(USE_TF='0', HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1')
    imports_started = time.perf_counter()
    import torch
    import laya
    import_seconds = time.perf_counter() - imports_started
    torch.set_num_threads(6)
    started = time.perf_counter()
    with warnings.catch_warnings(record=True) as captured:
        warnings.simplefilter('always')
        model = laya.load(str(args.runtime / 'models/laya-english'), device='cpu')
    load_seconds = time.perf_counter() - started
    questions = json.loads((ROOT / 'skills/laya-command/assets/command-questions.json').read_text(encoding='utf-8'))
    for item in items:
        samples = []
        for _ in range(3):
            started = time.perf_counter()
            result = model.predict(item['translation']['english'], questions)
            samples.append(time.perf_counter() - started)
            if result.get('usage', {}).get('truncated'):
                raise ValueError('Truncated benchmark input.')
        item['laya'] = result
        item['latency_seconds'] = samples
        item['matches_expected'] = result['answers']['request_type']['choice'] == item['expected']
    report = {'date': '2026-11-02', 'device': 'cpu', 'threads': 6,
              'hardware': {'cpu': 'Intel Core Ultra 5 225H', 'ram_gib': 15.53,
                           'gpu_used': False},
              'versions': {'laya': laya.__version__, 'torch': torch.__version__},
              'import_seconds': import_seconds, 'load_seconds': load_seconds,
              'warnings': [str(w.message) for w in captured],
              'translation_seconds': [x['translation']['elapsed_seconds'] for x in items],
              'inference_median_seconds': statistics.median([s for x in items for s in x['latency_seconds']]),
              'matches': sum(x['matches_expected'] for x in items), 'count': len(items),
              'items': items,
              'limitations': ['Four synthetic cases selected by the author; no held-out evaluation.',
                              'Translations reviewed by Codex, not an independent bilingual annotator.',
                              'Three sequential Laya calls per case; one process; includes first inference.',
                              'Peak memory and end-to-end Codex review time not measured.',
                              'Model scores are not verified probabilities of correctness.']}
    (args.output / 'results.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({k: v for k, v in report.items() if k != 'items'}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
