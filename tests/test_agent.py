import pytest
import json
from src.agent import run_agent_cycle

class CallTracker:
    def __init__(self):
        self.calls = []
    def __call__(self, *args, **kwargs):
        self.calls.append((args, kwargs))
        return "stubbed"

@pytest.fixture
def monkeypatch_state(tmp_path, monkeypatch_env, monkeypatch):
    # Patch state file location for load_state/save_state
    state_file = tmp_path / "state.json"
    state_file.write_text(json.dumps({}))
    from src import agent
    from src import utils
    monkeypatch.setattr(agent, "load_state", lambda: utils.load_state(str(state_file)))
    monkeypatch.setattr(agent, "save_state", lambda state: utils.save_state(state, str(state_file)))
    yield state_file

def test_new_world_news(monkeypatch, monkeypatch_state):
    # Case A: New world news topics
    tracker = CallTracker()
    monkeypatch.setattr("src.agent.fetch_world_news", lambda: [
        {"title": "A", "summary": "S", "url": "U"}
    ])
    monkeypatch.setattr("src.agent.fetch_x_trends", lambda: [])
    monkeypatch.setattr("src.agent.generate_blog_markdown", tracker)
    monkeypatch.setattr("src.agent.publish_blog", tracker)
    monkeypatch.setattr("src.agent.generate_tweet_thread", tracker)
    monkeypatch.setattr("src.agent.post_thread", tracker)
    run_agent_cycle()
    # All stubs should be called
    assert len(tracker.calls) >= 3
    # State should be updated
    with open(monkeypatch_state) as f:
        state = json.load(f)
    assert "last_hash" in state

def test_unchanged_world_news(monkeypatch, monkeypatch_state):
    # Case B: Unchanged topics
    # Set up state with hash for ["A"]
    from src.utils import compute_hash
    last_hash = compute_hash(["A"])
    with open(monkeypatch_state, "w") as f:
        json.dump({"last_hash": last_hash}, f)
    tracker = CallTracker()
    monkeypatch.setattr("src.agent.fetch_world_news", lambda: [
        {"title": "A", "summary": "S", "url": "U"}
    ])
    monkeypatch.setattr("src.agent.fetch_x_trends", lambda: [])
    monkeypatch.setattr("src.agent.generate_blog_markdown", tracker)
    monkeypatch.setattr("src.agent.publish_blog", tracker)
    monkeypatch.setattr("src.agent.generate_tweet_thread", tracker)
    monkeypatch.setattr("src.agent.post_thread", tracker)
    run_agent_cycle()
    # Blog/thread stubs should NOT be called
    assert len(tracker.calls) == 0

def test_x_only_trending(monkeypatch, monkeypatch_state):
    # Case C: X-only trending with >=50K tweets
    tracker = CallTracker()
    monkeypatch.setattr("src.agent.fetch_world_news", lambda: [
        {"title": "A", "summary": "S", "url": "U"}
    ])
    monkeypatch.setattr("src.agent.fetch_x_trends", lambda: [
        ("B", 60000), ("A", 100000)
    ])
    monkeypatch.setattr("src.agent.generate_blog_markdown", tracker)
    monkeypatch.setattr("src.agent.publish_blog", tracker)
    monkeypatch.setattr("src.agent.generate_tweet_thread", tracker)
    monkeypatch.setattr("src.agent.post_thread", tracker)
    run_agent_cycle()
    # Only generate_tweet_thread and post_thread should be called for "B"
    called_topics = [args[0][0] for args in tracker.calls if args[0]]
    assert "B" in called_topics 