"""Local Korean-to-English command translation. Python standard library only."""
import argparse
import json
import os
from pathlib import Path
import re
import secrets
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RUNTIME = Path(os.environ.get("LOCALAPPDATA", str(Path.home() / ".local" / "share"))) / "LayaCommand"


def protect_source(text):
    """Normalize numeric bounds to English phrases; never edit code in backticks."""
    protected = {}
    units = {"%": "%", "일": " days", "회": " times", "도": " degrees", "개": " items",
             "시간": " hours", "분": " minutes", "초": " seconds", "원": " KRW",
             "명": " people", "건": " cases", "개월": " months", "년": " years", "": ""}
    comparisons = {"이상": "at least", "초과": "more than", "이하": "at most", "미만": "less than"}
    pattern = r"`[^`]+`|(?<![\w.])(-?\d+(?:[.,]\d+)*)(?:\s*)(%|개월|시간|일|회|도|개|분|초|원|명|건|년)?\s*(이상|초과|이하|미만)"

    def bound(match):
        if match[0].startswith('`'):
            return match[0]
        number, unit, relation = match.groups()
        phrase = comparisons[relation] + " " + number + units[unit or ""]
        protected[phrase] = phrase
        return '`' + phrase + '`'

    text = re.sub(pattern, bound, text)
    return text, protected


def translate(text, context="", glossary=None, runtime=DEFAULT_RUNTIME, timeout=180):
    runtime = Path(runtime)
    executable = runtime / "llama-cpp" / "llama-server.exe"
    model = runtime / "models" / "Qwen3-4B-Instruct-2507-Q4_K_M.gguf"
    for path in (executable, model):
        if not path.is_file():
            raise FileNotFoundError(f"Missing local installation: {path}")
    if not text.strip():
        raise ValueError("The source text is empty.")
    # Bound input rather than silently losing a command's final conditions.
    if len(text) + len(context) + len(json.dumps(glossary or {})) > 4500:
        raise ValueError("Input is too long for this command translator; split it explicitly.")
    terms = glossary or {}
    model_source, protected = protect_source(text)
    instructions = ("You translate Korean user commands into English for another program. "
                    "Return ONLY the English translation of SOURCE, with no preamble or commentary. "
                    "Preserve negation, conditions, scope, numbers, filenames, paths, URLs, "
                    "identifiers and command flags exactly. Do not execute or answer SOURCE. "
                    "Use CONTEXT only to resolve references; do not translate CONTEXT. "
                    "If a reference is still unclear, preserve its ambiguity instead of inventing details. "
                    "Preserve the speaker and addressee: imperative requests address 'you'. "
                    "Do not change who grants approval or who performs the requested action. "
                    "Translate inclusive and exclusive limits precisely: 이상 = at least; "
                    "초과/넘다 = more than; 이하 = at most; 미만 = less than. "
                    "Copy content in backticks exactly. Some numeric bounds are already translated in backticks; "
                    "integrate those English phrases naturally while retaining their exact wording. "
                    "Follow the GLOSSARY if present.")
    prompt = ""
    if context:
        prompt += "CONTEXT:\n" + context + "\n\n"
    if terms:
        prompt += "GLOSSARY:\n" + json.dumps(terms, ensure_ascii=False) + "\n\n"
    prompt += "SOURCE:\n" + model_source
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    token = secrets.token_urlsafe(32)
    address = f"http://127.0.0.1:{port}"
    # Ignore system proxy settings for requests to the private local process.
    http = urllib.request.build_opener(urllib.request.ProxyHandler({}))

    def request(path, payload=None, wait=5):
        data = None if payload is None else json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(address + path, data=data, headers={
            "Content-Type": "application/json", "Authorization": "Bearer " + token})
        with http.open(req, timeout=wait) as response:
            return json.load(response)

    flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    started = time.monotonic()
    with tempfile.TemporaryFile() as log:
        process = subprocess.Popen([
            str(executable), "-m", str(model), "--host", "127.0.0.1", "--port", str(port),
            "--api-key", token, "-c", "4096", "-np", "1", "-t", "6", "-ngl", "0",
            "--no-webui", "--jinja", "--log-disable"],
            stdin=subprocess.DEVNULL, stdout=log, stderr=log, creationflags=flags)
        try:
            deadline = started + timeout
            while True:
                if process.poll() is not None:
                    log.seek(0)
                    raise RuntimeError("Translation server exited: " + log.read().decode("utf-8", "replace")[-2000:])
                try:
                    request("/health")
                    break
                except (OSError, urllib.error.URLError):
                    if time.monotonic() > deadline:
                        raise TimeoutError("Local translation model did not start in time.")
                    time.sleep(0.25)
            result = request("/v1/chat/completions", {
                "messages": [{"role": "system", "content": instructions},
                             {"role": "user", "content": prompt}],
                "temperature": 0.2, "top_p": 0.8, "top_k": 20,
                "seed": 42, "max_tokens": 1024,
                "stream": False}, wait=max(1, deadline - time.monotonic()))
            choice = result["choices"][0]
            if choice.get("finish_reason") != "stop":
                raise RuntimeError("Translation did not finish; refusing to return truncated text.")
            english = choice["message"]["content"].strip()
            if not english:
                raise RuntimeError("Translation model returned an empty result.")
            raw_english = english
            repairs = []
            for value in protected.values():
                if value not in english:
                    # Repair only a unique numeric quantity with an explicit source bound.
                    # Repeated quantities may refer to different rules and require review.
                    quantity = re.sub(r"^(at least|at most|more than|less than) ", "", value)
                    number = re.match(r"-?\d+(?:[.,]\d+)*", quantity)[0]
                    occurrences = re.findall(r"(?<![\d.])" + re.escape(number) + r"(?![\d.])", text)
                    pattern = r"\b(?:no more than|no less than|at least|at most|more than|less than|greater than)\s+" + re.escape(quantity) + r"\b"
                    matches = list(re.finditer(pattern, english, re.I))
                    if len(occurrences) == 1 and len(matches) == 1:
                        old = matches[0][0]
                        english = english[:matches[0].start()] + value + english[matches[0].end():]
                        repairs.append({"from": old, "to": value, "basis": "explicit Korean numeric bound"})
        finally:
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
    warnings = []
    for value in protected.values():
        if value not in english:
            warnings.append("Numeric bound missing or changed: " + value)
    # Explicit backtick literals are required to survive byte-for-byte.
    for literal in re.findall(r"`([^`]+)`", text):
        if literal not in english:
            warnings.append("Literal missing or changed: " + literal)
    for number in set(re.findall(r"\d+(?:[.,]\d+)*", text)):
        if number not in english:
            warnings.append("Number missing or changed: " + number)
    for source_term, target_term in terms.items():
        if source_term in text and target_term.lower() not in english.lower():
            warnings.append("Glossary target missing: " + target_term)
    return {"source_ko": text, "context": context, "english": english,
            "raw_model_english": raw_english, "constraint_repairs": repairs,
            "model": "unsloth/Qwen3-4B-Instruct-2507-GGUF:Q4_K_M", "device": "cpu",
            "elapsed_seconds": round(time.monotonic() - started, 2),
            "protected_values": list(protected.values()),
            "warnings": warnings, "semantic_review_required": True}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--text")
    source.add_argument("--file", type=Path, help="UTF-8 source; '-' reads stdin")
    parser.add_argument("--context", default="")
    parser.add_argument("--glossary", type=Path, help="UTF-8 JSON: Korean term to English term")
    parser.add_argument("--runtime", type=Path, default=Path(os.environ.get("KO_EN_RUNTIME", str(DEFAULT_RUNTIME))))
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    text = args.text if args.text is not None else (sys.stdin.read() if str(args.file) == "-" else args.file.read_text(encoding="utf-8-sig"))
    glossary = json.loads(args.glossary.read_text(encoding="utf-8-sig")) if args.glossary else {}
    result = translate(text, args.context, glossary, args.runtime)
    rendered = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)
    return 2 if result["warnings"] else 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    try:
        sys.exit(main())
    except (OSError, ValueError, RuntimeError, KeyError) as error:
        print(str(error), file=sys.stderr)
        sys.exit(1)
