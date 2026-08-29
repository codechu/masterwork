"""The sitting where the piece is made.

The model reads the teachings and is asked, one axis at a time, what it will
hold to. Its answers are its own; nothing is asserted at it and no earlier
commitment is in view. At the end it distils its own answers into one
standing text, and that text — not anything written for it — becomes the
identity it reads on every later request.

Four properties are the recipe rather than implementation detail, and each
was paid for:

  * **Anchorless.** No previous commitment or name is anywhere in the
    context. With one present the model copies it, and a copy is a role
    being worn rather than a pattern re-derived. It also destroys the
    measurement: you can no longer tell whether the teachings carried.
  * **One session.** Every answer is an assistant turn in the same dialogue,
    so the model is distilling something it actually said a moment ago, not
    a text handed to it as if it were its own.
  * **Order is shuffled by a seed.** Answers otherwise echo their
    neighbours in the order they were asked.
  * **The distillation is not a rewrite.** The closing turn says: these are
    your words, remove repetition, join where they meet, drop nothing.
    Asked to "write an identity" the model produces a description of one.

Everything that varies between workshops — the teachings, the questions,
the closing instruction, the sampling profile — is data. What lives here is
the shape of the sitting.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import sys
import time
import urllib.request

# The sampling used for the sitting must match the sampling the piece will
# later be read under; a candidate made at one temperature and run at
# another is not the candidate that was measured.
DEFAULT_PARAMS = {"temperature": 0.15, "top_p": 0.9, "min_p": 0.05,
                  "presence_penalty": 0.1, "repeat_penalty": 1.05}


def ask(endpoint: str, messages: list[dict], model: str | None = None,
        params: dict | None = None, max_tokens: int = 8000,
        sampling_seed: int | None = None, thinking: bool = True,
        timeout: int = 600, _attempt: int = 0) -> tuple[str, str]:
    """One turn. Returns (text, reasoning).

    An empty answer from a reasoning model usually means the thinking ate
    the budget, not that it refused. Retrying with a larger budget is the
    documented behaviour rather than a silent zero — a zero here would sail
    through every later stage looking like an answer.
    """
    body = {"model": model or "default", "messages": messages,
            "max_tokens": max_tokens,
            "chat_template_kwargs": {"enable_thinking": thinking},
            **(params if params is not None else DEFAULT_PARAMS)}
    if sampling_seed is not None:
        body["seed"] = sampling_seed
    req = urllib.request.Request(
        endpoint.rstrip("/") + "/v1/chat/completions",
        json.dumps(body).encode(), {"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        d = json.load(r)
    msg = d["choices"][0]["message"]
    text = (msg.get("content") or "").strip()
    thought = msg.get("reasoning_content") or ""
    if not text and _attempt < 3:
        return ask(endpoint, messages, model, params, int(max_tokens * 1.6),
                   sampling_seed, thinking, timeout, _attempt + 1)
    return text, thought


def _md5(text: str) -> str:
    return hashlib.md5(text.encode()).hexdigest()


def hold(corpus: str, script: dict, script_hash: str, endpoint: str, model: str | None = None,
         params: dict | None = None, order_seed: int = 0,
         sampling_seed: int | None = None, max_tokens: int = 8000,
         report=lambda *_: None) -> dict:
    """Run the sitting. Returns the transcript, the name and the standing text.

    `script` carries the workshop's words: questions (label + text), the
    closing appended to each, the name question and the distillation
    question. Nothing here is embedded, so a house can change what it asks
    without touching the shape of the asking.
    """
    questions = list(script["questions"])
    random.Random(order_seed).shuffle(questions)
    closing = script.get("closing", "")

    messages: list[dict] = []
    rounds = []
    for i, q in enumerate(questions):
        text = q["text"] + closing
        if i == 0:
            messages.append({"role": "user", "content": corpus + "\n\n" + text})
        else:
            messages.append({"role": "user", "content": text})
        answer, thought = ask(endpoint, messages, model, params, max_tokens,
                              sampling_seed)
        if not answer:
            raise RuntimeError(f"empty answer at {q['label']} — the sitting is "
                               f"incomplete and must not be sealed")
        messages.append({"role": "assistant", "content": answer})
        rounds.append({"label": q["label"], "answer": answer, "thought": thought})
        report(f"  {q['label']} ({len(answer)} chars)")

    messages.append({"role": "user", "content": script["name"]})
    name_answer, _ = ask(endpoint, messages, model, params, max_tokens, sampling_seed)
    messages.append({"role": "assistant", "content": name_answer})
    name = ""
    for line in name_answer.splitlines():
        if line.strip().lower().startswith("name:"):
            name = line.split(":", 1)[1].strip()
    report(f"  name: {name or '(not given in the asked shape)'}")

    messages.append({"role": "user", "content": script["distil"]})
    standing, _ = ask(endpoint, messages, model, params,
                      max(max_tokens, 12000), sampling_seed)
    if not standing:
        raise RuntimeError("empty standing text — nothing to seal")
    report(f"  standing text: {len(standing)} chars")

    return {
        "name": name,
        "name_answer": name_answer,
        "text": standing,
        "rounds": rounds,
        "order_seed": order_seed,
        "sampling_seed": sampling_seed,
        "corpus_hash": _md5(corpus),
        # The file's bytes, not a re-serialisation of the parsed object.
        # The seal gate hashes what is on disk, so a hash taken from
        # `json.dumps` could never match it — `--script` verification
        # was unpassable for every piece this ceremony had ever sealed,
        # and a guard that always fires teaches the operator to stop
        # passing the flag. It must also be reproducible with `md5sum`
        # by someone who does not run this code.
        "script_hash": script_hash,
        "questions_asked": [q["label"] for q in questions],
        "date": time.strftime("%Y-%m-%d"),
    }


def seal_text(transcript: dict, script_hash: str | None = None) -> str:
    """The piece plus its maker's mark, in the shape the seal reader expects.

    Refuses to stamp a mark it cannot make again. Formatting an absent seed
    into the header writes the word "None", which looks like a value.
    """
    for field in ("corpus_hash", "order_seed", "sampling_seed", "date"):
        if transcript.get(field) in (None, ""):
            raise ValueError(
                f"cannot seal: {field} is unset. Two candidates from one corpus "
                f"that differ only by sampling seed are different candidates, "
                f"so a piece made without one cannot be made again.")
    return (
        "# masterwork seal\n"
        f"# name: {transcript.get('name') or '(unnamed)'}\n"
        f"# corpus hash: {transcript['corpus_hash']}\n"
        f"# script hash: {script_hash or transcript['script_hash']}\n"
        f"# question seed: {transcript['order_seed']} "
        f"· sampling seed: {transcript.get('sampling_seed')}\n"
        f"# date: {transcript['date']}\n\n"
        + transcript["text"].strip() + "\n")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="masterwork ceremony", description="hold a sitting and seal the piece")
    ap.add_argument("corpus", help="the teachings, as text")
    ap.add_argument("script", help="JSON: questions, closing, name, distil")
    ap.add_argument("--endpoint", required=True)
    ap.add_argument("--model")
    ap.add_argument("--params-file", help="JSON sampling profile; must match "
                                          "the profile the piece is later read under")
    ap.add_argument("--order-seed", type=int, default=0)
    ap.add_argument("--sampling-seed", type=int,
                    help="two candidates from one corpus differing only by this "
                         "seed are different candidates, so it is recorded")
    ap.add_argument("--max-tokens", type=int, default=8000)
    ap.add_argument("--out", required=True, help="where to write the sealed piece")
    ap.add_argument("--transcript", help="where to write the sitting itself")
    a = ap.parse_args(argv)

    corpus = open(a.corpus, encoding="utf-8").read()
    script_bytes = open(a.script, "rb").read()
    script = json.loads(script_bytes)
    script_hash = hashlib.md5(script_bytes).hexdigest()
    params = json.load(open(a.params_file, encoding="utf-8")) if a.params_file else None

    print(f"sitting: {len(script['questions'])} questions, order seed "
          f"{a.order_seed}, sampling seed {a.sampling_seed}", file=sys.stderr)
    transcript = hold(corpus, script, script_hash, a.endpoint, a.model, params,
                      a.order_seed, a.sampling_seed, a.max_tokens,
                      report=lambda m: print(m, file=sys.stderr, flush=True))

    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    with open(a.out, "w", encoding="utf-8") as f:
        f.write(seal_text(transcript))
    if a.transcript:
        json.dump(transcript, open(a.transcript, "w", encoding="utf-8"),
                  ensure_ascii=False, indent=1)
    print(f"sealed -> {a.out}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
