import pytest
import logging
from src import twitter_api

class DummyStatus:
    def __init__(self, id_str, text=None, user=None, created_at=None):
        self.id_str = id_str
        self.text = text or "tweet text"
        self.full_text = text or "tweet text"
        self.user = type("User", (), {"screen_name": user or "testuser"})()
        self.created_at = created_at or "2024-01-01T00:00:00Z"

class DummyTrends:
    def __init__(self):
        self.trends = [{"name": "#Nigeria", "tweet_volume": 12345}, {"name": "#Lagos", "tweet_volume": 6789}]

class DummyReply:
    def __init__(self, id_str, text, user, in_reply_to_status_id_str, created_at):
        self.id_str = id_str
        self.text = text
        self.full_text = text
        self.user = type("User", (), {"screen_name": user})()
        self.in_reply_to_status_id_str = in_reply_to_status_id_str
        self.created_at = created_at

class DummyCursor:
    def __init__(self, *a, **k):
        self.items_list = [
            DummyReply("r1", "reply1", "user1", "t1", "2024-01-01T00:00:00Z"),
            DummyReply("r2", "reply2", "user2", "t1", "2024-01-01T01:00:00Z")
        ]
    def items(self, n):
        return self.items_list

class DummyClient:
    def update_status(self, status, in_reply_to_status_id=None, auto_populate_reply_metadata=None):
        return DummyStatus("1234567890", text=status, user="testuser")
    def get_status(self, tweet_id, tweet_mode=None):
        return DummyStatus(tweet_id, text="tweet text", user="testuser")
    def get_place_trends(self, woeid):
        return [{"trends": DummyTrends().trends}]
    def media_upload(self, filename):
        class Media:
            media_id = 123
        return Media()

@pytest.fixture(autouse=True)
def patch_logging(monkeypatch):
    monkeypatch.setattr(logging, "info", lambda *a, **k: None)
    monkeypatch.setattr(logging, "error", lambda *a, **k: None)

@pytest.fixture(autouse=True)
def patch_cursor(monkeypatch):
    monkeypatch.setattr(twitter_api.tweepy, "Cursor", lambda *a, **k: DummyCursor())

@pytest.fixture
def patch_client(monkeypatch):
    monkeypatch.setattr(twitter_api, "get_twitter_client", lambda: DummyClient())


def test_post_thread_success(patch_client):
    tweets = ["tweet1", "tweet2"]
    ids = twitter_api.post_thread(tweets)
    assert ids == ["1234567890", "1234567890"]

def test_post_thread_error(monkeypatch, patch_client):
    class FailingClient(DummyClient):
        def update_status(self, *a, **k):
            raise Exception("fail")
    monkeypatch.setattr(twitter_api, "get_twitter_client", lambda: FailingClient())
    ids = twitter_api.post_thread(["tweet1"])
    assert ids == []

def test_post_response_success(patch_client):
    tweet_id = twitter_api.post_response("hello", "123")
    assert tweet_id == "1234567890"

def test_post_response_error(monkeypatch, patch_client):
    class FailingClient(DummyClient):
        def update_status(self, *a, **k):
            raise Exception("fail")
    monkeypatch.setattr(twitter_api, "get_twitter_client", lambda: FailingClient())
    tweet_id = twitter_api.post_response("hello", "123")
    assert tweet_id == ""

def test_fetch_replies_success(patch_client, monkeypatch):
    # Patch tweepy.Cursor to return a list with at least one reply
    class PatchedReply:
        def __init__(self):
            self.id_str = "r1"
            self.text = "reply1"
            self.full_text = "reply1"
            self.user = type("User", (), {"screen_name": "user1"})()
            self.in_reply_to_status_id_str = "t1"
            self.created_at = "2024-01-01T00:00:00Z"
    class PatchedCursor:
        def __init__(self, *a, **k):
            pass
        def items(self, n):
            return [PatchedReply()]
    monkeypatch.setattr(twitter_api.tweepy, "Cursor", lambda *a, **k: PatchedCursor())
    replies = twitter_api.fetch_replies("t1")
    assert isinstance(replies, list)
    assert replies[0]["id"] == "r1"
    assert replies[0]["user"] == "user1"

def test_fetch_replies_error(monkeypatch, patch_client):
    class FailingClient(DummyClient):
        def get_status(self, *a, **k):
            raise Exception("fail")
    monkeypatch.setattr(twitter_api, "get_twitter_client", lambda: FailingClient())
    replies = twitter_api.fetch_replies("t1")
    assert replies == []

def test_fetch_tweet_success(patch_client):
    tweet = twitter_api.fetch_tweet("t1")
    assert tweet["id"] == "t1"
    assert tweet["user"] == "testuser"

def test_fetch_tweet_error(monkeypatch, patch_client):
    class FailingClient(DummyClient):
        def get_status(self, *a, **k):
            raise Exception("fail")
    monkeypatch.setattr(twitter_api, "get_twitter_client", lambda: FailingClient())
    tweet = twitter_api.fetch_tweet("t1")
    assert tweet["id"] == "t1"
    assert tweet["text"] == ""

def test_fetch_trending_topics_success(patch_client):
    topics = twitter_api.fetch_trending_topics()
    assert isinstance(topics, list)
    assert topics[0][0] == "#Nigeria"
    assert topics[0][1] == 12345

def test_fetch_trending_topics_error(monkeypatch, patch_client):
    class FailingClient(DummyClient):
        def get_place_trends(self, *a, **k):
            raise Exception("fail")
    monkeypatch.setattr(twitter_api, "get_twitter_client", lambda: FailingClient())
    topics = twitter_api.fetch_trending_topics()
    assert topics == [] 