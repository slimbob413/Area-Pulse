"""
twitter_api.py

Native Twitter/X API integration for NaijaPulseBot using Tweepy.
Provides functions for posting threads, replying, fetching tweets/replies, and trending topics.
All functions log success and errors, and return output compatible with Grok-based utils.
"""

import os
import logging
from typing import List, Optional, Tuple, Dict
import tweepy

DRY_RUN = os.getenv("DRY_RUN", "false").lower() == "true"

_client = None

def get_twitter_client() -> tweepy.API:
    """
    Returns a Tweepy API client, initializing it if necessary.
    Reads credentials from environment variables.
    Raises RuntimeError if any required env var is missing.
    """
    global _client
    if _client is not None:
        return _client
    TWITTER_API_KEY = os.getenv("TWITTER_API_KEY")
    TWITTER_API_SECRET = os.getenv("TWITTER_API_SECRET")
    TWITTER_ACCESS_TOKEN = os.getenv("TWITTER_ACCESS_TOKEN")
    TWITTER_ACCESS_TOKEN_SECRET = os.getenv("TWITTER_ACCESS_TOKEN_SECRET")
    if not all([TWITTER_API_KEY, TWITTER_API_SECRET, TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_TOKEN_SECRET]):
        raise RuntimeError("Twitter API credentials are not fully set in environment variables.")
    auth = tweepy.OAuth1UserHandler(
        TWITTER_API_KEY,
        TWITTER_API_SECRET,
        TWITTER_ACCESS_TOKEN,
        TWITTER_ACCESS_TOKEN_SECRET
    )
    _client = tweepy.API(auth)
    return _client

def post_thread(tweets: List[str], in_reply_to: Optional[str] = None) -> List[str]:
    """
    Posts a thread of tweets. Returns a list of tweet IDs.
    """
    if DRY_RUN:
        logging.info(f"[DRY_RUN] Would have posted thread: {tweets}")
        return ["dry_run_tweet_id"] * len(tweets)
    tweet_ids = []
    last_tweet_id = in_reply_to
    try:
        api = get_twitter_client()
        for i, tweet in enumerate(tweets):
            status = api.update_status(status=tweet, in_reply_to_status_id=last_tweet_id, auto_populate_reply_metadata=True if last_tweet_id else False)
            tweet_ids.append(status.id_str)
            last_tweet_id = status.id_str
            logging.info(f"Posted tweet {i+1}/{len(tweets)}: {status.id_str}")
        return tweet_ids
    except Exception as e:
        logging.error(f"Failed to post tweet thread: {e}")
        return tweet_ids

def post_response(text: str, in_reply_to: str) -> str:
    """
    Posts a reply to a specific tweet. Returns the new tweet ID.
    """
    if DRY_RUN:
        logging.info(f"[DRY_RUN] Would have posted response: '{text}' in reply to {in_reply_to}")
        return "dry_run_tweet_id"
    try:
        api = get_twitter_client()
        status = api.update_status(status=text, in_reply_to_status_id=in_reply_to, auto_populate_reply_metadata=True)
        logging.info(f"Posted response tweet: {status.id_str}")
        return status.id_str
    except Exception as e:
        logging.error(f"Failed to post response: {e}")
        return ""

def fetch_replies(tweet_id: str) -> List[dict]:
    """
    Fetches replies to a tweet. Returns a list of dicts: {id, user, text, timestamp}
    """
    try:
        api = get_twitter_client()
        tweet = api.get_status(tweet_id, tweet_mode="extended")
        username = tweet.user.screen_name
        replies = []
        for reply in tweepy.Cursor(api.search_tweets, q=f'to:{username}', since_id=tweet_id, tweet_mode='extended').items(100):
            if hasattr(reply, 'in_reply_to_status_id_str') and reply.in_reply_to_status_id_str == tweet_id:
                replies.append({
                    "id": reply.id_str,
                    "user": reply.user.screen_name,
                    "text": getattr(reply, 'full_text', reply.text),
                    "timestamp": str(reply.created_at)
                })
        logging.info(f"Fetched {len(replies)} replies for tweet {tweet_id}.")
        return replies
    except Exception as e:
        logging.error(f"Failed to fetch replies for tweet {tweet_id}: {e}")
        return []

def fetch_tweet(tweet_id: str) -> dict:
    """
    Fetches a single tweet by ID. Returns dict: {id, text, user}
    """
    try:
        api = get_twitter_client()
        tweet = api.get_status(tweet_id, tweet_mode="extended")
        result = {
            "id": tweet.id_str,
            "text": getattr(tweet, 'full_text', tweet.text),
            "user": tweet.user.screen_name
        }
        logging.info(f"Fetched tweet {tweet_id}.")
        return result
    except Exception as e:
        logging.error(f"Failed to fetch tweet {tweet_id}: {e}")
        return {"id": tweet_id, "text": "", "user": ""}

def fetch_trending_topics() -> List[Tuple[str, int]]:
    """
    Fetches trending topics for Nigeria (WOEID 23424908). Returns list of (topic, tweet_count).
    """
    try:
        api = get_twitter_client()
        trends = api.get_place_trends(23424908)
        topics = []
        for trend in trends[0]["trends"]:
            name = trend["name"]
            count = trend.get("tweet_volume") or 0
            topics.append((name, int(count)))
        logging.info(f"Fetched {len(topics)} trending topics for Nigeria.")
        return topics
    except Exception as e:
        logging.error(f"Failed to fetch trending topics: {e}")
        return [] 