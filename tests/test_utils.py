import os
import json
import hashlib
import pytest
from src.utils import compute_hash, load_state, save_state, fetch_world_news, fetch_x_trends

class DummyResponse:
    def __init__(self, json_data):
        self._json = json_data
    def json(self):
        return self._json
    def raise_for_status(self):
        pass

def test_compute_hash():
    topics = ["A", "B", "C"]
    expected = hashlib.sha256("A|B|C".encode("utf-8")).hexdigest()
    assert compute_hash(topics) == expected

def test_load_save_state(tmp_path, monkeypatch_env):
    state_file = tmp_path / "state.json"
    state = {"foo": 123}
    save_state(state, str(state_file))
    loaded = load_state(str(state_file))
    assert loaded == state

def test_fetch_world_news(monkeypatch, monkeypatch_env):
    fake_json = {"news": [
        {"title": "T1", "text": "S1", "url": "U1"},
        {"title": "T2", "text": "S2", "url": "U2"}
    ]}
    monkeypatch.setattr("requests.get", lambda *a, **k: DummyResponse(fake_json))
    result = fetch_world_news()
    assert result == [
        {"title": "T1", "summary": "S1", "url": "U1"},
        {"title": "T2", "summary": "S2", "url": "U2"}
    ]

def test_fetch_x_trends(monkeypatch, monkeypatch_env):
    fake_json = {"trends": [
        {"name": "Topic1", "tweet_volume": 100000},
        {"name": "Topic2", "tweet_volume": 50000}
    ]}
    monkeypatch.setattr("requests.get", lambda *a, **k: DummyResponse(fake_json))
    result = fetch_x_trends()
    assert result == [("Topic1", 100000), ("Topic2", 50000)] 