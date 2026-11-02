"""Pass a reviewed English translation to the installed local Laya checkpoint."""
import argparse
import json
import os
from pathlib import Path
import sys
import time


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--translation", required=True, type=Path)
    parser.add_argument("--questions", required=True, type=Path,
                        help="English Laya question schema; option IDs remain unchanged")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--runtime", type=Path, default=Path(os.environ.get("KO_EN_RUNTIME",
                        str(Path(os.environ.get("LOCALAPPDATA", str(Path.home() / ".local" / "share"))) / "LayaCommand"))))
    args = parser.parse_args()
    translation = json.loads(args.translation.read_text(encoding="utf-8-sig"))
    if translation.get("warnings"):
        raise ValueError("Resolve translation warnings before passing it to Laya.")
    state = translation["english"]
    if not isinstance(state, str) or not state.strip():
        raise ValueError("English translation is empty.")
    questions = json.loads(args.questions.read_text(encoding="utf-8-sig"))
    os.environ["HF_HOME"] = str(args.runtime / "hf-cache")
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"
    os.environ['USE_TF'] = '0'
    started = time.perf_counter()
    import torch
    import laya
    import_seconds = time.perf_counter() - started
    torch.set_num_threads(6)
    started = time.perf_counter()
    model = laya.load(str(args.runtime / "models/laya-english"), device="cpu")
    load_seconds = time.perf_counter() - started
    started = time.perf_counter()
    result = model.predict(state, questions)
    inference_seconds = time.perf_counter() - started
    if result.get("usage", {}).get("truncated"):
        raise ValueError("Laya truncated input; shorten the request/schema explicitly.")
    payload = {"translation": translation, "questions": questions, "laya": result,
               "timing": {"import_seconds": import_seconds, "load_seconds": load_seconds,
                          "inference_seconds": inference_seconds},
               "note": "Model scores are not verified probabilities of correctness."}
    rendered = json.dumps(payload, ensure_ascii=False, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
