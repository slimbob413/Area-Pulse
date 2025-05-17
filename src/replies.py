"""
replies.py

Handles engagement and reply automation for NaijaPulseBot.

This module contains the run_engagement_bot function, which executes every 10 minutes to:
- Fetch new replies and mentions.
- Classify and prioritize engagement.
- Generate and post responses.
"""

import logging
from src.utils import load_state, save_state, fetch_replies, fetch_tweet, classify_reply, generate_reply_text, post_response

def run_engagement_bot():
    """
    Every 10 minutes:
    - Load state: responded_reply_ids (List[str]), bot_tweet_ids (List[str])
    - For each tweet_id in bot_tweet_ids:
        • replies = fetch_replies(tweet_id)
        • original = fetch_tweet(tweet_id)
        • For each reply in replies:
            - If reply['id'] not in responded_reply_ids:
                → label = classify_reply(reply['text'])
                → If label in ['question','disagreement','support']:
                    * response = generate_reply_text(reply, original)
                    * new_id = post_response(response, reply['id'])
                    * Log success
                → Else:
                    * Log skipping label
                → Add reply['id'] to responded_reply_ids
    - Save updated state
    """
    logging.info("Starting engagement bot loop.")
    state = load_state()
    responded = set(state.get("responded_reply_ids", []))
    bot_tweets = state.get("bot_tweet_ids", [])
    for tweet_id in bot_tweets:
        replies = fetch_replies(tweet_id)
        original = fetch_tweet(tweet_id)
        for reply in replies:
            if reply["id"] in responded:
                continue
            try:
                label = classify_reply(reply["text"])
                if label in ("question", "disagreement", "support"):
                    response = generate_reply_text(reply, original)
                    new_id = post_response(response, reply["id"])
                    logging.info(f"Replied to {reply['id']} with {new_id}")
                else:
                    logging.debug(f"Skipping reply {reply['id']} labeled {label}")
            except Exception as e:
                logging.error(f"Error handling reply {reply['id']}: {e}")
            responded.add(reply["id"])
    # Save updated state
    state["responded_reply_ids"] = list(responded)
    save_state(state)
    logging.info("Engagement bot loop complete.") 