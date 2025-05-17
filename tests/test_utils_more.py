import re
import os
import pytest
from src.utils import generate_blog_markdown, generate_tweet_thread, publish_blog, post_thread, analyze_sentiment

class DummyRepo:
    def __init__(self, repo_path):
        self.repo_path = repo_path
        self.git = self
        self.index = self
    def pull(self): pass
    def add(self, filename): self.added = filename
    def commit(self, msg): self.committed = msg
    def push(self): self.pushed = True

class DummyPath:
    def __init__(self, *a, **k): pass
    def mkdir(self, *a, **k): pass
    def __truediv__(self, other): return self
    def __str__(self): return "dummy_path"
    def write_text(self, content): self.content = content
    def write_bytes(self, content): self.content = content
    @property
    def parent(self):
        return self

@pytest.fixture(autouse=True)
def patch_env(monkeypatch):
    monkeypatch.setenv("GITHUB_REPO_PATH", "/tmp/repo")
    monkeypatch.setenv("BLOG_BASE_URL", "https://testblog.com")
    yield

def test_generate_blog_markdown_blocks():
    md = generate_blog_markdown("Test Topic", "Summary here", "positive")
    assert md.startswith("# Test Topic")
    assert "Overall public sentiment" in md
    assert "<!-- ADSENSE_PLACEHOLDER -->" in md
    assert "AFFILIATE_URL" in md and "PATREON_LINK" in md
    assert "## Introduction" in md and "## Conclusion" in md

def test_generate_tweet_thread_content():
    tweets = generate_tweet_thread("TestTopic", ["sent1", "sent2"])
    assert tweets[0].startswith("\U0001F4E2 Hot Topic")
    assert any("Read the full story" in t for t in tweets)
    assert 5 <= len(tweets) <= 7

def test_publish_blog_gitpython(monkeypatch):
    # Patch Repo and Path
    monkeypatch.setattr("src.utils.Repo", DummyRepo)
    monkeypatch.setattr("src.utils.Path", DummyPath)
    class DummyFile:
        def __enter__(self): return self
        def __exit__(self, *a): pass
        def write(self, content): self.content = content
    orig_open = open
    def fake_open(f, mode="r", *a, **k):
        if isinstance(f, DummyPath):
            return DummyFile()
        return orig_open(f, mode, *a, **k)
    monkeypatch.setattr("builtins.open", fake_open)
    url = publish_blog("# Blog", "Test Topic")
    assert url.startswith("https://testblog.com/_posts/")

def test_post_thread(monkeypatch):
    posted = []
    def fake_post(url, headers=None, json=None, timeout=None):
        class Resp:
            def raise_for_status(self): pass
            def json(self): return {"id": f"id_{len(posted)}"}
        posted.append(json["text"])
        return Resp()
    monkeypatch.setenv("GROK_API_KEY", "dummy_key")
    monkeypatch.setattr("requests.post", fake_post)
    tweets = [f"tweet {i}" for i in range(3)]
    post_thread(tweets, reply_to=None)
    assert posted == ["tweet 0", "tweet 1", "tweet 2"]

def test_analyze_sentiment_positive(monkeypatch):
    class DummyChoice:
        text = "positive"
    class DummyResp:
        choices = [DummyChoice()]
    def fake_create(*a, **k):
        return DummyResp()
    monkeypatch.setenv("OPENAI_KEY", "dummy")
    import openai
    monkeypatch.setattr(openai.Completion, "create", fake_create)
    result = analyze_sentiment("Nigeria is booming!")
    assert result == "positive" 