# Model selection — 2026-11-02

Chosen: [Qwen3-4B-Instruct-2507](https://huggingface.co/Qwen/Qwen3-4B-Instruct-2507), Unsloth's [Q4_K_M GGUF](https://huggingface.co/unsloth/Qwen3-4B-Instruct-2507-GGUF), `Qwen3-4B-Instruct-2507-Q4_K_M.gguf`, 2,497,281,120 bytes. Apache-2.0 model license. Use a translator system instruction, separate SOURCE/CONTEXT/GLOSSARY, and llama.cpp's structured chat endpoint. This is an instruction model used as a translator. No claim that it outperforms dedicated translation models has been measured here. The quantized weights are provided by Unsloth, not directly by Qwen.

Runtime: [llama.cpp](https://github.com/ggml-org/llama.cpp), official Windows CPU x64 binaries, b11960. CPU selected to verify compatibility with this specific Windows 11 machine without assuming Intel GPU support. 15.5 GiB total RAM; available RAM varied around 3 GiB during setup. Translation and Laya should run sequentially.

Other candidates investigated:

- [Qwen3-1.7B Q8_0](https://huggingface.co/Qwen/Qwen3-1.7B-GGUF): actually installed and tested, then rejected. A test changed the approval/sending actor; another turned “3 days or more” into “more than 3 days”. Literal/number checks did not catch these semantic mistakes. Its weights were removed after preserving test evidence. This motivated choosing the 4B model and retaining semantic review.

- [HY-MT1.5-1.8B](https://huggingface.co/tencent/HY-MT1.5-1.8B-GGUF): translation-specialized and supports contextual/terminology prompts. Rejected after its actual License.txt explicitly excluded South Korea from its territory. Its downloaded model weight was removed; no HY model is selected by this skill.
- [Hy-MT2](https://huggingface.co/collections/tencent/hy-mt2): official models start at 7B, too large for the current preferred local footprint; no inference installed.
- [TranslateGemma 4B](https://huggingface.co/google/translategemma-4b-it): larger and uses Gemma-specific terms. No gated agreement accepted and no model installed.
- [OPUS-MT ko-en](https://huggingface.co/Helsinki-NLP/opus-mt-ko-en): Apache-2.0 dedicated Korean/English model; compact alternative, but its older sentence translation interface does not offer the same instruction-based context/glossary control. Not installed or comparatively benchmarked.
- [Argos Translate](https://github.com/argosopentech/argos-translate): offline translation software alternative; not installed or comparatively benchmarked.

Known limits: small local models can mistranslate negation, scope and references. Context helps but cannot recover unstated intent reliably. Even the 4B model initially changed “3 days or more” to “more than 3 days”. The helper normalizes numeric bounds with 이상/초과/이하/미만 before inference, repairs a changed comparator only when its numeric quantity is unique in source and output, and records raw output and the exact repair. Missing/ambiguous bounds produce warnings instead. It also checks backtick literals and numeric substrings; it does not prove semantic equivalence. It rejects empty/oversized input and incomplete generation. It does not execute translated commands or globally intercept Laya/Codex input. The skill applies only when selected by Codex or explicitly invoked.

Downloaded GGUF SHA-256 matched the publisher's Hugging Face LFS object ID: `3605803b982cb64aead44f6c1b2ae36e3acdb41d8e46c8a94c6533bc4c67e597`.
