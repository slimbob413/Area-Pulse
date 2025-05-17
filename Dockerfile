# Dockerfile for NaijaPulseBot
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code and config/state/logs
COPY src/ ./src/
COPY main.py ./
COPY state/ ./state/
COPY logs/ ./logs/
COPY config/ ./config/

# Set environment variables (placeholders, can be overridden)
ENV GROK_API_KEY=your_grok_api_key_here \
    OPENAI_KEY=your_openai_key_here \
    WORLD_NEWS_KEY=your_world_news_key_here \
    GITHUB_REPO_PATH=/app/repo \
    BLOG_BASE_URL=https://yourblog.com \
    ADSENSE_ID=your_adsense_id_here \
    STRIPE_KEY=your_stripe_key_here \
    PATREON_KEY=your_patreon_key_here

# Healthcheck: ensure state/state.json updated within 3 hours
HEALTHCHECK --interval=30m --timeout=30s CMD python src/healthcheck.py

# Default command
CMD ["python", "main.py"] 