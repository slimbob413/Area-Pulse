import os
import shutil
import tempfile
import pytest

@pytest.fixture
def temp_state_dir(tmp_path):
    # Create a temporary state directory and state.json file
    state_dir = tmp_path / "state"
    state_dir.mkdir()
    state_file = state_dir / "state.json"
    state_file.write_text("{}\n")
    yield state_dir

@pytest.fixture
def monkeypatch_env(monkeypatch):
    monkeypatch.setenv("GROK_API_KEY", "test_grok_key")
    monkeypatch.setenv("OPENAI_KEY", "test_openai_key")
    monkeypatch.setenv("WORLD_NEWS_KEY", "test_world_news_key")
    monkeypatch.setenv("GITHUB_REPO_PATH", "/tmp/repo")
    monkeypatch.setenv("BLOG_BASE_URL", "https://testblog.com")
    monkeypatch.setenv("ADSENSE_ID", "test_adsense")
    monkeypatch.setenv("STRIPE_KEY", "test_stripe")
    monkeypatch.setenv("PATREON_KEY", "test_patreon")
    yield 