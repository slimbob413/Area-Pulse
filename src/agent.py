import logging
import os
ENABLE_X_TRENDS = os.getenv("ENABLE_X_TRENDS", "false").lower() == "true"
from src.utils import (
    fetch_world_news,
    fetch_x_trends,
    compute_hash,
    load_state,
    save_state,
    generate_seo_blog_post,
    publish_blog,
    generate_tweet_thread,
    post_thread,
    log_metric,
    analyze_sentiment,
    generate_blog_image,
    fetch_primary_trend_keyword,
)

"""
agent.py

Defines the main agent loop for NaijaPulseBot.

This module contains the run_agent_cycle function, which executes the following steps every 2 hours:
1. Fetch trending topics and news.
2. Summarize and analyze sentiment.
3. Generate blog and tweet content.
4. Publish blog and post thread.
5. Update state and log actions.
"""

def run_agent_cycle():
    """
    Executes the main agent cycle:
    1. Fetch trending topics and world news.
    2. For each new news article, generate blog markdown, publish blog, and post tweet thread.
    3. Update persistent state and log actions.
    4. X trends logic is unchanged.
    """
    try:
        logging.info("Starting agent cycle.")
        os.makedirs("logs", exist_ok=True)
        # Fetch world news
        news = fetch_world_news()[:3]  # limit to 3 articles per cycle
        state = load_state()
        # Use a list of hashes for per-article deduplication
        title_hashes = state.get("title_hashes", [])
        processed_hashes = set(title_hashes)
        new_hashes = []
        any_published = False

        # Early exit if all fetched news already processed
        if not news:
            logging.info("World News API returned no articles. Nothing to process.")
            return

        # Determine primary Google trend keyword once per cycle (fallback handled in util)
        primary_trend_keyword = fetch_primary_trend_keyword()

        for idx, article in enumerate(news):
            try:
                title = article.get("title", f"Nigeria News {idx+1}")
                summary = article.get("summary", "Summary unavailable.")
                article_hash = compute_hash([title])
                if article_hash in processed_hashes:
                    logging.info(f"Skipping already-processed article: {title}")
                    continue
                sentiment = analyze_sentiment(title)
                image_url = generate_blog_image(title)
                md = generate_seo_blog_post(title, primary_trend_keyword, image_url=image_url)
                blog_url = publish_blog(md, title, premium_only=False)
                estimated_cost = 0.01  # TODO: Replace with real cost calculation
                log_metric("api_spend_usd", estimated_cost)
                thread = generate_tweet_thread(title, sentiment)
                post_thread(thread, reply_to=None)
                log_metric("tweets_published", 1)
                new_hashes.append(article_hash)
                logging.info(f"Processed and published article: {title} (Blog: {blog_url})")
                any_published = True
            except Exception as e:
                logging.error(f"Failed to process article '{article.get('title', 'Unknown')}': {e}")
        # Update state with all new hashes
        if new_hashes:
            state["title_hashes"] = title_hashes + new_hashes
            save_state(state)
            logging.info(f"State updated with {len(new_hashes)} new article hashes.")
        elif not any_published:
            logging.info("No unseen world news articles to process. Skipping cycle.")
            return  # Exit early
        # Fetch X trends
        titles = [item["title"] for item in news]
        if ENABLE_X_TRENDS:
            raw_trends = fetch_x_trends()
            x_trends = [(topic, count, analyze_sentiment(topic)) for topic, count in raw_trends]
            world_news_top2 = set(titles[:2])
            for topic, count, sentiment in x_trends:
                if topic in world_news_top2:
                    continue
                if count >= 50000:
                    logging.info(f"Trending topic '{topic}' with {count} tweets meets threshold. Generating thread.")
                    try:
                        thread = generate_tweet_thread(topic, sentiment)
                        post_thread(thread, reply_to=None)
                        log_metric("tweets_published", 1)
                    except Exception as e:
                        logging.error(f"Failed to generate or post X-only thread for '{topic}': {e}")
                else:
                    logging.debug(f"Trending topic '{topic}' below threshold: {count} tweets.")
        else:
            logging.info("X-trend posting is disabled via ENABLE_X_TRENDS=false")
        logging.info("Agent cycle complete.")
    except Exception as e:
        logging.error(f"run_agent_cycle encountered an error: {e}")
        return 