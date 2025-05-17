"""
utils.py

Utility functions for NaijaPulseBot.

Includes API wrappers, content generators, state management, and hashing utilities.
"""

import os
import requests
import json
import hashlib
import logging
from typing import List, Tuple, Dict, Optional
from datetime import datetime
from pathlib import Path
import re
import time, functools
from random import uniform
try:
    from git import Repo
except ImportError:
    Repo = None  # For environments without GitPython
from openai import OpenAI
import subprocess

USE_NATIVE_TWITTER = os.getenv("USE_NATIVE_TWITTER", "false").lower() == "true"
if USE_NATIVE_TWITTER:
    from src import twitter_api

DRY_RUN = os.getenv("DRY_RUN", "false").lower() == "true"

STATE_PATH = os.getenv("STATE_PATH", "state/state.json")

METRIC_LOG_PATH = os.getenv("METRIC_LOG_PATH", "logs/metrics.csv")

def retry(max_attempts=3, initial_delay=1.0, backoff_factor=2.0, jitter=0.1):
    """
    Retry decorator with exponential back-off and jitter.
    """
    def wrapper(fn):
        @functools.wraps(fn)
        def inner(*args, **kwargs):
            delay = initial_delay
            for attempt in range(1, max_attempts + 1):
                try:
                    return fn(*args, **kwargs)
                except Exception as e:
                    if attempt == max_attempts:
                        raise
                    logging.warning(f"Retrying {fn.__name__} (attempt {attempt}/{max_attempts}) after error: {e}")
                    time.sleep(delay + uniform(0, jitter))
                    delay *= backoff_factor
        return inner
    return wrapper

@retry()
def fetch_world_news() -> List[Dict[str, str]]:
    """
    Fetches world news articles from the World News API for Nigeria.
    Reads WORLD_NEWS_KEY from environment.
    Returns a list of dicts: [{"title": str, "summary": str, "url": str}]
    Logs errors and returns an empty list on failure.
    """
    api_key = os.getenv("WORLD_NEWS_KEY")
    if not api_key:
        logging.error("WORLD_NEWS_KEY not set in environment.")
        raise RuntimeError("WORLD_NEWS_KEY not set in environment.")
    url = "https://api.worldnewsapi.com/search-news"
    params = {
        "api-key": api_key,
        "text": "Nigeria",
        "language": "en",
        "number": 5,
        "sort": "publish-time"
    }
    try:
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        articles = []
        for item in data.get("news", []):
            articles.append({
                "title": item.get("title", ""),
                "summary": item.get("text", ""),
                "url": item.get("url", "")
            })
        logging.info(f"Fetched {len(articles)} Nigeria news articles.")
        return articles
    except Exception as e:
        logging.error(f"Failed to fetch world news: {e}")
        return []

@retry()
def fetch_x_trends() -> List[Tuple[str, int]]:
    """
    Fetches trending topics from Grok/X API or native Twitter API for Nigeria.
    Returns a list of (topic, tweet_count) tuples.
    Logs errors and returns an empty list on failure.
    """
    if USE_NATIVE_TWITTER:
        return twitter_api.fetch_trending_topics()
    api_key = os.getenv("GROK_API_KEY")
    if not api_key:
        logging.error("GROK_API_KEY not set in environment.")
        raise RuntimeError("GROK_API_KEY not set in environment.")
    url = "https://grok.x.com/api/v1/trends/place"
    params = {"id": 23424908}  # WOEID for Nigeria
    headers = {"Authorization": f"Bearer {api_key}"}
    try:
        resp = requests.get(url, params=params, headers=headers, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        trends = []
        for item in data.get("trends", []):
            name = item.get("name")
            count = item.get("tweet_volume") or 0
            if name:
                trends.append((name, int(count)))
        logging.info(f"Fetched {len(trends)} X trending topics for Nigeria.")
        return trends
    except Exception as e:
        logging.error(f"Failed to fetch X trends: {e}")
        return []

def compute_hash(topics: List[str]) -> str:
    """
    Computes an SHA256 hash of the joined topic titles.
    Returns the hex digest string.
    """
    joined = "|".join(topics)
    hash_val = hashlib.sha256(joined.encode("utf-8")).hexdigest()
    logging.debug(f"Computed hash for topics: {hash_val}")
    return hash_val

def load_state(state_path: str = STATE_PATH) -> dict:
    """
    Loads persistent state from the given path (default: STATE_PATH).
    Returns the state dict, or {} if missing/corrupt.
    """
    try:
        with open(state_path, "r") as f:
            state = json.load(f)
            logging.debug(f"Loaded state from {state_path}.")
            return state
    except FileNotFoundError:
        logging.warning(f"{state_path} not found. Initializing empty state.")
        return {}
    except Exception as e:
        logging.error(f"Failed to load state: {e}")
        return {}

def save_state(state: dict, state_path: str = STATE_PATH):
    """
    Saves persistent state to the given path (default: STATE_PATH).
    Ensures the parent directory exists before saving.
    """
    try:
        Path(state_path).parent.mkdir(parents=True, exist_ok=True)
        with open(state_path, "w") as f:
            json.dump(state, f, indent=2)
        logging.info(f"State saved to {state_path}.")
    except Exception as e:
        logging.error(f"Failed to save state: {e}")

OPENAI_KEY = os.getenv("OPENAI_KEY")
OPENAI_TEXT_MODEL = os.getenv("OPENAI_TEXT_MODEL", "gpt-4-1106-preview")
client = None
if OPENAI_KEY:
    client = OpenAI(api_key=OPENAI_KEY)

def analyze_sentiment(text: str) -> str:
    """
    Use OpenAI to classify sentiment as 'positive', 'neutral', or 'negative'.
    Returns the label (lowercased).
    """
    if not client:
        logging.error("OPENAI_KEY not set in environment or OpenAI client not initialized.")
        raise RuntimeError("OPENAI_KEY not set in environment.")
    prompt = (
        "Classify the sentiment of this text as one of: positive, neutral, or negative.\n"
        f"Text: {text}\nRespond with only the label."
    )
    try:
        response = client.chat.completions.create(
            model=OPENAI_TEXT_MODEL,
            messages=[{"role": "system", "content": "You are a sentiment analysis assistant."},
                      {"role": "user", "content": prompt}],
            max_tokens=10
        )
        label = response.choices[0].message.content.strip().lower()
        if label not in ("positive", "neutral", "negative"):
            label = "neutral"
        logging.info(f"Sentiment for '{text}': {label}")
        return label
    except Exception as e:
        if hasattr(e, 'status_code') and e.status_code == 401:
            logging.error("OpenAI authentication failed: Invalid API key.")
        else:
            logging.error(f"Failed to analyze sentiment: {e}")
        return "neutral"

def generate_blog_image(prompt: str) -> str:
    """
    Generate an image using OpenAI's DALL·E API and return the image URL.
    Reads OPENAI_KEY, OPENAI_IMAGE_MODEL, and OPENAI_IMAGE_SIZE from env.
    """
    if not client:
        logging.error("OPENAI_KEY not set in environment or OpenAI client not initialized.")
        raise RuntimeError("OPENAI_KEY not set in environment.")
    model = os.getenv("OPENAI_IMAGE_MODEL", "dall-e-3")
    size = os.getenv("OPENAI_IMAGE_SIZE", "1024x1024")
    try:
        response = client.images.generate(
            model=model,
            prompt=prompt,
            n=1,
            size=size
        )
        image_url = response.data[0].url
        logging.info(f"Generated image for prompt '{prompt}': {image_url}")
        return image_url
    except Exception as e:
        if hasattr(e, 'status_code') and e.status_code == 401:
            logging.error("OpenAI authentication failed: Invalid API key.")
        else:
            logging.error(f"Failed to generate image: {e}")
        return ""

def generate_blog_markdown(topic: str, summary: str, sentiment: str, image_url: str = None) -> str:
    """
    Build a Markdown news article with a human-crafted headline, narrative style, and monetization links.
    - Headline is original and not a direct reuse of the topic string.
    - Article is a single narrative, paragraph-based report (no subheads or placeholders).
    - If image_url is provided, it appears at the top.
    - Markdown starts with a ##-level headline, then date, sentiment, then the article body, ending with monetization links.
    """
    import random

    # Simple headline generator: rephrase topic for a more human, journalistic headline
    def make_headline(topic):
        templates = [
            "Inside Nigeria: {}",
            "What You Need to Know About {}",
            "{}: The Latest Developments",
            "Unpacking {}",
            "Nigeria Focus: {}",
            "{} – A Closer Look",
            "{}: What Happened and Why It Matters",
            "Breaking Down {}",
            "{}: Key Insights This Week",
            "{}: A News Report"
        ]
        # Remove trailing punctuation and capitalize
        base = topic.strip().rstrip('.!?')
        template = random.choice(templates)
        return template.format(base)

    date_str = datetime.utcnow().strftime("%Y-%m-%d")
    headline = make_headline(topic)
    image_md = f"![news image]({image_url})\n" if image_url else ""
    # Compose the markdown
    md = f"""## {headline}
{image_md}_Date: {date_str}_  
_Sentiment: {sentiment}_

{summary}

Support us: [Patreon](PATREON_LINK) | [Tip Jar](TIP_JAR)
"""
    return md

def generate_tweet_thread(topic: str, sentiment: str) -> list:
    """
    Return a list of 5–7 tweet strings for a thread about the topic and sentiment.
    Prepends a line with the overall public sentiment.
    """
    tweets = []
    tweets.append(f"\U0001F4E2 Hot Topic: {topic}\nPublic sentiment: **{sentiment}**")
    key_points = [
        f"Key point {i+1} about {topic}. Sentiment: {sentiment}."
        for i in range(5)
    ]
    tweets.extend(key_points)
    tweets.append("Read the full story: BLOG_URL \nSupport us: Patreon | Tip Jar")
    return tweets

def generate_insider_brief(topic: str, summary: str, sentiment: str) -> str:
    """
    Return a 300-word markdown "insider" section for paying subscribers.
    """
    # TODO: implement LLM call for premium content
    return "# Insider Brief\n\n<!-- TODO: flesh out premium analysis -->"

@retry()
def publish_blog(markdown: str, topic: str, premium_only: bool = False) -> str:
    """
    Publishes the generated blog markdown to the blog platform (GitHub Pages repo).
    If premium_only is True, writes to private_posts/; else to _posts/ (Jekyll standard).
    Returns the public URL of the new post.
    Reads STRIPE_KEY from env; stub for Stripe product creation.
    Uses DRY_RUN to skip git commit/push but log what would happen.
    """
    repo_path = os.getenv("GITHUB_REPO_PATH")
    blog_base_url = os.getenv("BLOG_BASE_URL")
    github_token = os.getenv("GITHUB_TOKEN")
    if not repo_path or not blog_base_url:
        logging.error("GITHUB_REPO_PATH or BLOG_BASE_URL not set in environment.")
        raise RuntimeError("GITHUB_REPO_PATH or BLOG_BASE_URL not set in environment.")
    if Repo is None:
        logging.error("GitPython is not installed.")
        raise RuntimeError("GitPython is not installed.")
    date_str = datetime.utcnow().strftime("%Y-%m-%d")
    slug = re.sub(r'[^a-z0-9]+', '-', topic.lower()).strip('-')
    if premium_only:
        filename = f"private_posts/{date_str}-{slug}.md"
        # Read STRIPE_KEY from env and create Stripe product (stub)
        stripe_key = os.getenv("STRIPE_KEY")
        # TODO: Integrate with Stripe API to create/check product for this post
    else:
        filename = f"_posts/{date_str}-{slug}.md"
    post_path = Path(repo_path) / filename
    post_path.parent.mkdir(parents=True, exist_ok=True)
    with open(post_path, "w", encoding="utf-8") as f:
        f.write(markdown)
    url = f"{blog_base_url}/{filename}"
    if DRY_RUN:
        logging.info(f"[DRY_RUN] Would have committed and pushed blog post: {filename} to {repo_path}")
        logging.info(f"[DRY_RUN] Blog post URL would be: {url}")
        return url
    try:
        repo = Repo(repo_path)
        repo.git.add(filename)
        repo.index.commit(f"Add blog post: {topic}")
        # Use GITHUB_TOKEN for authentication in push
        origin_url = repo.remotes.origin.url
        if github_token and origin_url.startswith("https://"):
            # Insert token into URL for push
            if "@" not in origin_url:
                origin_url = origin_url.replace("https://", f"https://{github_token}@")
            repo.git.push(origin_url, "HEAD:main")
        else:
            repo.git.push()
        logging.info(f"Published blog post: {url}")
        return url
    except Exception as e:
        logging.error(f"Failed to publish blog post: {e}")
        raise

@retry()
def post_thread(tweets: List[str], reply_to: Optional[str]) -> None:
    """
    Posts a thread of tweets to X (Twitter) using Grok/X API or native Twitter API.
    If reply_to is provided, links the first tweet to that ID.
    Logs tweet IDs.
    """
    if DRY_RUN:
        logging.info(f"[DRY_RUN] Would have posted thread: {tweets}")
        return ["dry_run_tweet_id"] * len(tweets)
    if USE_NATIVE_TWITTER:
        twitter_api.post_thread(tweets, in_reply_to=reply_to)
        return
    api_key = os.getenv("GROK_API_KEY")
    if not api_key:
        logging.error("GROK_API_KEY not set in environment.")
        raise RuntimeError("GROK_API_KEY not set in environment.")
    url = "https://grok.x.com/api/v1/tweets"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    last_tweet_id = reply_to
    tweet_ids = []
    try:
        for i, tweet in enumerate(tweets):
            payload = {"text": tweet}
            if last_tweet_id:
                payload["in_reply_to_status_id"] = last_tweet_id
            resp = requests.post(url, headers=headers, json=payload, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            tweet_id = data.get("id_str") or data.get("id")
            if tweet_id:
                tweet_ids.append(tweet_id)
                last_tweet_id = tweet_id
                logging.info(f"Posted tweet {i+1}/{len(tweets)}: {tweet_id}")
            else:
                logging.warning(f"No tweet ID returned for tweet {i+1}.")
    except Exception as e:
        logging.error(f"Failed to post tweet thread: {e}")

@retry()
def fetch_replies(tweet_id: str) -> List[Dict]:
    """
    Call the Grok/X API or native Twitter API to fetch recent replies to the given tweet ID.
    Returns a list of reply dicts: {
        "id": str,
        "user": str,
        "text": str,
        "timestamp": str
    }
    """
    if USE_NATIVE_TWITTER:
        return twitter_api.fetch_replies(tweet_id)
    api_key = os.getenv("GROK_API_KEY")
    if not api_key:
        logging.error("GROK_API_KEY not set in environment.")
        raise RuntimeError("GROK_API_KEY not set in environment.")
    url = f"https://api.grok.ai/v1/tweets/{tweet_id}/replies"
    headers = {"Authorization": f"Bearer {api_key}"}
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        replies = []
        for r in data.get("replies", []):
            replies.append({
                "id": r.get("id"),
                "user": r.get("user", {}).get("username", ""),
                "text": r.get("text", ""),
                "timestamp": r.get("created_at", "")
            })
        logging.info(f"Fetched {len(replies)} replies for tweet {tweet_id}.")
        return replies
    except Exception as e:
        logging.error(f"Failed to fetch replies for tweet {tweet_id}: {e}")
        return []

@retry()
def fetch_tweet(tweet_id: str) -> Dict:
    """
    Fetch a single tweet by ID from Grok/X API or native Twitter API.
    Returns a dict: {"id": id, "text": text, "user": username}
    """
    if USE_NATIVE_TWITTER:
        return twitter_api.fetch_tweet(tweet_id)
    api_key = os.getenv("GROK_API_KEY")
    if not api_key:
        logging.error("GROK_API_KEY not set in environment.")
        raise RuntimeError("GROK_API_KEY not set in environment.")
    url = f"https://api.grok.ai/v1/tweets/{tweet_id}"
    headers = {"Authorization": f"Bearer {api_key}"}
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        tweet = {
            "id": data.get("id"),
            "text": data.get("text", ""),
            "user": data.get("user", {}).get("username", "")
        }
        logging.info(f"Fetched tweet {tweet_id}.")
        return tweet
    except Exception as e:
        logging.error(f"Failed to fetch tweet {tweet_id}: {e}")
        return {"id": tweet_id, "text": "", "user": ""}

def classify_reply(text: str) -> str:
    """
    Classify a reply into one of: 'question', 'disagreement', 'support', 'spam', or 'other'.
    Uses OpenAI ChatCompletion for classification.
    """
    if not client:
        logging.error("OPENAI_KEY not set in environment or OpenAI client not initialized.")
        raise RuntimeError("OPENAI_KEY not set in environment.")
    prompt = (
        "Classify the following tweet reply as one of: 'question', 'disagreement', 'support', 'spam', or 'other'. "
        "Respond with only the label.\n\nReply: " + text
    )
    try:
        response = client.chat.completions.create(
            model=OPENAI_TEXT_MODEL,
            messages=[{"role": "system", "content": "You are a tweet reply classifier."},
                      {"role": "user", "content": prompt}],
            max_tokens=10
        )
        label = response.choices[0].message.content.strip().lower()
        if label not in ("question", "disagreement", "support", "spam", "other"):
            label = "other"
        logging.info(f"Classified reply as: {label}")
        return label
    except Exception as e:
        if hasattr(e, 'status_code') and e.status_code == 401:
            logging.error("OpenAI authentication failed: Invalid API key.")
        else:
            logging.error(f"Failed to classify reply: {e}")
        return "other"

def generate_reply_text(reply: Dict, original_tweet: Dict) -> str:
    """
    Given a reply dict and the original bot tweet dict, send a GPT-4 prompt to generate
    a concise, respectful response under 280 characters.
    Returns the reply text.
    """
    if not client:
        logging.error("OPENAI_KEY not set in environment or OpenAI client not initialized.")
        raise RuntimeError("OPENAI_KEY not set in environment.")
    prompt = (
        f"You are @NaijaPulseBot. A user said: \"{reply['text']}\". "
        f"The original tweet was: \"{original_tweet['text']}\". "
        "Generate a respectful, fact-based reply under 280 characters."
    )
    try:
        response = client.chat.completions.create(
            model=OPENAI_TEXT_MODEL,
            messages=[{"role": "system", "content": "You are a helpful, concise Twitter bot."},
                      {"role": "user", "content": prompt}],
            max_tokens=60
        )
        reply_text = response.choices[0].message.content.strip()
        logging.info(f"Generated reply text: {reply_text}")
        return reply_text
    except Exception as e:
        if hasattr(e, 'status_code') and e.status_code == 401:
            logging.error("OpenAI authentication failed: Invalid API key.")
        else:
            logging.error(f"Failed to generate reply text: {e}")
        return "Thank you for your reply! We'll consider your input."

@retry()
def post_response(text: str, in_reply_to: str) -> str:
    """
    Post the given text as a reply to the specified tweet ID via Grok/X API or native Twitter API.
    Returns the new tweet ID.
    """
    if DRY_RUN:
        logging.info(f"[DRY_RUN] Would have posted response: '{text}' in reply to {in_reply_to}")
        return "dry_run_tweet_id"
    if USE_NATIVE_TWITTER:
        return twitter_api.post_response(text, in_reply_to)
    api_key = os.getenv("GROK_API_KEY")
    if not api_key:
        logging.error("GROK_API_KEY not set in environment.")
        raise RuntimeError("GROK_API_KEY not set in environment.")
    url = "https://api.grok.ai/v1/tweets"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {"text": text, "reply_to": in_reply_to}
    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        tweet_id = data.get("id")
        if tweet_id:
            logging.info(f"Posted response tweet: {tweet_id}")
            return tweet_id
        else:
            logging.warning("No tweet ID returned after posting response.")
            return ""
    except Exception as e:
        logging.error(f"Failed to post response: {e}")
        return ""

def log_metric(name: str, value: float):
    """
    Append a metric to the log file specified by METRIC_LOG_PATH: timestamp,name,value
    """
    with open(METRIC_LOG_PATH, "a") as f:
        f.write(f"{datetime.utcnow().isoformat()},{name},{value}\n") 