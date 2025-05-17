import pytest
import logging
from src.agent import run_agent_cycle

class DummyLogger:
    def __init__(self):
        self.records = []
    def info(self, msg): self.records.append(("info", msg))
    def error(self, msg): self.records.append(("error", msg))
    def debug(self, msg): self.records.append(("debug", msg))

@pytest.fixture(autouse=True)
def patch_logging(monkeypatch):
    logger = DummyLogger()
    monkeypatch.setattr(logging, "info", logger.info)
    monkeypatch.setattr(logging, "error", logger.error)
    monkeypatch.setattr(logging, "debug", logger.debug)
    yield logger

def test_run_agent_cycle_handles_fetch_error(monkeypatch, patch_logging):
    # Simulate fetch_world_news raising
    monkeypatch.setattr("src.agent.fetch_world_news", lambda: (_ for _ in ()).throw(Exception("fail!")))
    monkeypatch.setattr("src.agent.fetch_x_trends", lambda: [])
    # Stubs for all other calls
    monkeypatch.setattr("src.agent.generate_blog_markdown", lambda *a, **k: "")
    monkeypatch.setattr("src.agent.publish_blog", lambda *a, **k: "")
    monkeypatch.setattr("src.agent.generate_tweet_thread", lambda *a, **k: [])
    monkeypatch.setattr("src.agent.post_thread", lambda *a, **k: None)
    # Should not raise
    try:
        run_agent_cycle()
    except Exception:
        pytest.fail("run_agent_cycle should not crash on fetch error")
    # Should log error
    assert any("fail!" in msg for lvl, msg in patch_logging.records if lvl == "error")

def test_run_agent_cycle_x_only_below_threshold(monkeypatch, patch_logging):
    import logging
    monkeypatch.setenv("OPENAI_KEY", "dummy")
    logging.getLogger().setLevel(logging.DEBUG)
    # Simulate world news and X trends with <50K
    monkeypatch.setattr("src.agent.fetch_world_news", lambda: [
        {"title": "A", "summary": "S", "url": "U"}
    ])
    monkeypatch.setattr("src.agent.fetch_x_trends", lambda: [("B", 40000)])
    monkeypatch.setattr("src.agent.generate_blog_markdown", lambda *a, **k: "")
    monkeypatch.setattr("src.agent.publish_blog", lambda *a, **k: "")
    monkeypatch.setattr("src.agent.generate_tweet_thread", lambda *a, **k: [])
    monkeypatch.setattr("src.agent.post_thread", lambda *a, **k: None)
    run_agent_cycle()
    # Should log debug for below threshold
    try:
        assert any("below threshold" in msg for lvl, msg in patch_logging.records if lvl == "debug")
    except AssertionError:
        print("DEBUG LOGS:", patch_logging.records)
        raise 