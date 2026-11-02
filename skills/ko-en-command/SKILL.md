---
name: ko-en-command
description: Translate Korean instructions into context-preserving English for Laya or another English-oriented tool, using the installed local Qwen model and reviewing negation, conditions and literal values before handoff.
---

# Korean commands to English

Use the installed local Qwen3-4B-Instruct-2507 Q4_K_M model through llama.cpp. This is an Apache-2.0 general language model configured for translation, not a translation-only model. No cloud API key is needed. The helper starts a private localhost process for one request, then stops it before Laya loads.

## Translate

Run `scripts/translate.ps1` with `-Text`, or use `-InputFile` for a UTF-8 file. For substantial or quoted input, prefer a file so PowerShell cannot interpolate the user's text. Pass relevant earlier conversation with `-Context`; do not invent missing context. An optional `-Glossary` accepts a UTF-8 JSON map from Korean terms to exact English terms.

```powershell
& "$env:USERPROFILE/.codex/skills/ko-en-command/scripts/translate.ps1" -Text '삭제하지 말고 목록만 보여줘.'
```

The JSON result contains the original, English translation, runtime, and literal/number warnings. Exit code 2 means a warning requires correction; 1 means inference failed. Never silently substitute an online translator when local inference fails.

Before handing the English to Laya, compare the source and translation for:

- who does what, the intended object, and references such as “that”;
- prohibition versus permission, “only”, “unless”, conditions, and action order;
- numbers, units, filenames, paths, flags, and user-defined terms;
- omitted conditions or invented scope.

Put paths, commands and identifiers in backticks in source files when possible: the helper checks their exact preservation. It converts numeric phrases using 이상/초과/이하/미만 and supported units to explicit English phrases before inference. If the model changes a comparator for a numeric quantity that appears only once in the source and once in output, the helper repairs that comparator from the source and records `constraint_repairs`; the untouched output remains in `raw_model_english`. Repeated or missing quantities are left for review and produce warnings. Warnings are partial checks, not proof of semantic correctness. Resolve other demonstrated translation errors with a targeted glossary/context change or an explicitly identified Codex correction. Preserve the raw local model output when reporting a correction. If ambiguity matters and the conversation cannot resolve it, ask only for that missing meaning.

## Optional Laya handoff

Translate state text and question instructions/option descriptions into English. Keep schema keys, IDs, numeric bounds, and option IDs unchanged. Use the user's actual question schema; do not infer a task just to get a result. Laya returns decisions and scores; it does not execute arbitrary PC commands. A high model score is not a verified probability of correctness.

The existing Laya installation is at `%LOCALAPPDATA%/LayaCommand/.venv/Scripts/python.exe`; the English checkpoint is in that runtime's `models/laya-english`. Finish translation first and let its server exit before loading Laya to limit memory use.

After reviewing a saved translation, run `scripts/laya_predict.py --translation TRANSLATION.json --questions QUESTIONS.json --output RESULT.json` using that Python executable. It runs entirely offline with the downloaded English checkpoint and refuses warning-bearing translations or truncated Laya results. Keep the original Korean and the translation alongside the decisions for review.

## Local installation

The helper defaults to `%LOCALAPPDATA%/LayaCommand`. Override with `KO_EN_RUNTIME` or the Python helper's `--runtime` after relocating the model and binaries. It requires `llama-cpp/llama-server.exe`, its adjacent DLLs, and `models/Qwen3-4B-Instruct-2507-Q4_K_M.gguf`. Read [references/selection.md](references/selection.md) for model sources, selection reasons and tested limitations.
