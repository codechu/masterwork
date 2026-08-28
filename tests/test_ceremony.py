"""The sitting. The tests are about its shape, which is the recipe."""
import json
import os
import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pipeline import ceremony, seal  # noqa: E402

SCRIPT = {
    "questions": [{"label": "A", "text": "question A"},
                  {"label": "B", "text": "question B"},
                  {"label": "C", "text": "question C"}],
    "closing": "\n(closing)",
    "name": "your name?",
    "distil": "these are your words; join them, drop nothing",
}


class Stub(BaseHTTPRequestHandler):
    seen: list = []
    empties: int = 0

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        Stub.seen.append(body)
        last = body["messages"][-1]["content"]
        if "name?" in last:
            text = "it must carry the work\nName: Wright"
        elif "join them" in last:
            text = "the standing text"
        elif Stub.empties > 0:
            Stub.empties -= 1
            text = ""          # a reasoning model that spent the budget thinking
        else:
            text = f"answer to {last.strip().splitlines()[0][:12]}"
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(
            {"choices": [{"message": {"content": text}}]}).encode())

    def log_message(self, *_):
        pass


def serve():
    s = HTTPServer(("127.0.0.1", 0), Stub)
    threading.Thread(target=s.serve_forever, daemon=True).start()
    return s, f"http://127.0.0.1:{s.server_port}"


def test_the_sitting_is_one_session_and_nothing_is_anchored():
    """Every answer is an assistant turn in the same chain, and no prior
    commitment appears anywhere: a copy would be a role, not a pattern."""
    Stub.seen = []
    s, url = serve()
    try:
        t = ceremony.hold("THE TEACHINGS", SCRIPT, url, order_seed=1, sampling_seed=7)
    finally:
        s.shutdown()
    assert len(t["rounds"]) == 3
    assert t["name"] == "Wright" and t["text"] == "the standing text"
    final_chain = Stub.seen[-1]["messages"]
    roles = [m["role"] for m in final_chain]
    assert roles[0] == "user" and roles.count("assistant") == 4
    assert "THE TEACHINGS" in final_chain[0]["content"]
    assert not any("commitment of" in m["content"] for m in final_chain)
    assert all(b.get("seed") == 7 for b in Stub.seen)


def test_order_is_shuffled_by_the_seed():
    """Answers echo their neighbours in the order asked, so the order moves."""
    orders = []
    for seed in (0, 1, 2, 3, 4):
        Stub.seen = []
        s, url = serve()
        try:
            orders.append(tuple(ceremony.hold("t", SCRIPT, url,
                                              order_seed=seed)["questions_asked"]))
        finally:
            s.shutdown()
    assert len(set(orders)) > 1


def test_an_empty_answer_is_retried_not_recorded_as_silence():
    """A reasoning model that spends its budget thinking returns nothing;
    a zero here would pass every later stage looking like an answer."""
    Stub.seen = []
    Stub.empties = 1
    s, url = serve()
    try:
        t = ceremony.hold("t", SCRIPT, url)
    finally:
        s.shutdown()
        Stub.empties = 0
    assert all(r["answer"] for r in t["rounds"])


def test_the_sealed_piece_passes_the_seal_gate(tmp_path=None):
    """What the sitting writes must be readable by the gate that guards it."""
    import tempfile
    Stub.seen = []
    s, url = serve()
    try:
        t = ceremony.hold("THE TEACHINGS", SCRIPT, url, order_seed=2, sampling_seed=11)
    finally:
        s.shutdown()
    with tempfile.TemporaryDirectory() as tmp:
        piece = os.path.join(tmp, "candidate.txt")
        open(piece, "w").write(ceremony.seal_text(t))
        corpus = os.path.join(tmp, "corpus.md")
        open(corpus, "w").write("THE TEACHINGS")
        assert seal.read_seal(piece).complete
        assert not seal.verify(piece, corpus=corpus)
