import pytest
import time
import json
from src.utils import fetch_replies, fetch_tweet, classify_reply, generate_reply_text, post_response
from src.replies import run_engagement_bot

class DummyResponse:
    def __init__(self, json_data):
        self._json = json_data
    def json(self):
        return self._json
    def raise_for_status(self):
        pass

def test_fetch_replies(monkeypatch, monkeypatch_env):
    fake_json = {"replies": [
        {"id": "1", "user": {"username": "u1"}, "text": "hi", "created_at": "now"}
    ]}
    monkeypatch.setattr("requests.get", lambda *a, **k: DummyResponse(fake_json))
    replies = fetch_replies("123")
    assert replies == [{"id": "1", "user": "u1", "text": "hi", "timestamp": "now"}]

def test_fetch_tweet(monkeypatch, monkeypatch_env):
    fake_json = {"id": "1", "user": {"username": "u1"}, "text": "tweet!"}
    monkeypatch.setattr("requests.get", lambda *a, **k: DummyResponse(fake_json))
    tweet = fetch_tweet("1")
    assert tweet == {"id": "1", "user": "u1", "text": "tweet!"}

def test_classify_reply(monkeypatch, monkeypatch_env):
    class DummyChoice:
        def __init__(self, text):
            self.text = text
    class DummyResp:
        def __init__(self, text):
            self.choices = [DummyChoice(text)]
    monkeypatch.setattr("openai.Completion.create", lambda *a, **k: DummyResp("support"))
    label = classify_reply("Thanks!")
    assert label == "support"

def test_generate_reply_text(monkeypatch, monkeypatch_env):
    class DummyChoice:
        def __init__(self, text):
            self.text = text
    class DummyResp:
        def __init__(self, text):
            self.choices = [DummyChoice(text)]
    monkeypatch.setattr("openai.Completion.create", lambda *a, **k: DummyResp("Thanks for your reply!"))
    reply = {"text": "hi"}
    orig = {"text": "tweet!"}
    text = generate_reply_text(reply, orig)
    assert text == "Thanks for your reply!"

def test_post_response(monkeypatch, monkeypatch_env):
    class DummyResp:
        def json(self): return {"id": "999"}
        def raise_for_status(self): pass
    monkeypatch.setattr("requests.post", lambda *a, **k: DummyResp())
    tweet_id = post_response("hi", "1")
    assert tweet_id == "999"

def test_run_engagement_bot(monkeypatch, tmp_path, monkeypatch_env):
    # Setup state
    state_file = tmp_path / "state.json"
    state = {"responded_reply_ids": [], "bot_tweet_ids": ["t1"]}
    state_file.write_text(json.dumps(state))
    # Patch utils in replies
    from src import replies
    replies_path = "src.replies"
    # Simulate 3 replies: question, spam, support
    fake_replies = [
        {"id": "r1", "user": "u1", "text": "?", "timestamp": "now"},
        {"id": "r2", "user": "u2", "text": "buy now", "timestamp": "now"},
        {"id": "r3", "user": "u3", "text": "great!", "timestamp": "now"}
    ]
    monkeypatch.setattr(replies, "fetch_replies", lambda tid: fake_replies)
    monkeypatch.setattr(replies, "fetch_tweet", lambda tid: {"id": tid, "text": "tweet!", "user": "bot"})
    # Classify: r1=question, r2=spam, r3=support
    def classify(text):
        if text == "?": return "question"
        if text == "buy now": return "spam"
        if text == "great!": return "support"
        return "other"
    monkeypatch.setattr(replies, "classify_reply", classify)
    posted = []
    monkeypatch.setattr(replies, "generate_reply_text", lambda r, o: f"reply to {r['id']}")
    monkeypatch.setattr(replies, "post_response", lambda text, rid: posted.append((text, rid)) or f"id_{rid}")
    # Patch state file usage
    monkeypatch.setattr(replies, "load_state", lambda: json.loads(state_file.read_text()))
    monkeypatch.setattr(replies, "save_state", lambda s: state_file.write_text(json.dumps(s)))
    run_engagement_bot()
    # Only r1 and r3 should be posted
    assert posted == [("reply to r1", "r1"), ("reply to r3", "r3")]
    # State should be updated
    updated = json.loads(state_file.read_text())
    assert set(updated["responded_reply_ids"]) == {"r1", "r2", "r3"} 