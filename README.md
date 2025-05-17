![Coverage](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/slimbob413/<GIST_ID>/raw/coverage-badge.json)

# NaijaPulseBot – Unified Automation & Blog

This repository contains both the automation logic and the GitHub Pages blog for NaijaPulseBot.

## Overview

NaijaPulseBot is an autonomous agent that curates, summarizes, and engages with Nigerian news. It fetches world news and X (Twitter) trends, generates content (blog + tweet threads), publishes to GitHub Pages/X, and runs an engagement bot to reply to users. The project is containerized, supports premium content, and is continuously validated via CI.

## Stack & Workflow

1. **News Fetch**: Pulls top Nigerian news from World News API.
2. **OpenAI**: Analyzes sentiment and generates summaries/images (DALL·E).
3. **Content Generation**: Produces blog posts (Markdown) and tweet threads.
4. **Publishing**:
   - Blog posts are saved to `_posts/` for Jekyll/GitHub Pages.
   - Premium content (if enabled) goes to `private_posts/`.
   - Tweet threads are posted to X (Twitter) via API.
5. **State & Metrics**: Tracks processed articles and logs API usage.
6. **Deployment**:
   - **GitHub Pages** serves the blog from `_posts/`.
   - **Render** or similar can deploy the full app from this directory.

## Setup

- All code, state, and blog content live in this directory.
- Requires a `.env` file (not tracked in git) with API keys and config.
- See `.gitignore` for ignored files/folders.

## Running

- Run `python3 main.py` to start the agent.
- Blog posts will appear in `_posts/` and be published via GitHub Pages.
- State and logs are managed in `state/` and `logs/`.

## Notes
- Do **not** commit your `.env` file.
- All automation and blog content are unified for easy deployment and management.

## Features
- Fetches world news and X (Twitter) trends
- Summarizes and analyzes sentiment
- Generates blog markdown and tweet threads
- Publishes content and engages with replies
- Runs on a schedule using APScheduler
- Monetization hooks for AdSense, Stripe, and Patreon

## Premium Content
NaijaPulseBot supports paid premium content via the "Insider Brief" feature. When enabled, the bot generates exclusive, in-depth analysis for paying subscribers. Premium posts are written to the `private_posts/` directory and require a valid Stripe integration.

- Set the `STRIPE_KEY` environment variable with your Stripe secret key.
- (Planned) Each premium post will be associated with a Stripe product for access control.
- To enable paid access, configure your static site generator or backend to restrict `private_posts/` to authenticated/paid users.

**Note:** Stripe integration is stubbed; see code comments in `publish_blog()` for where to add product creation/check logic.

## CI/CD
- GitHub Actions workflow: `.github/workflows/ci.yml`
  - Linting (`flake8`)
  - Tests (`pytest`)
  - Coverage enforcement (≥80%)
  - Docker build
- To run locally:
  ```bash
  pytest --cov=src --cov-report=term-missing
  docker-compose up --build
  ```

## Testing & Coverage

Run the full test suite with coverage:
```bash
pytest --cov=src --cov-report=term-missing
```

## Folder Structure
```
config/
  └── .env.example
state/
  └── state.json
src/
  ├── agent.py
  ├── replies.py
  ├── utils.py
  └── models/
main.py
requirements.txt
README.md
.gitignore
```

## Next Steps
- Implement API integrations in `utils.py`
- Fill in business logic in `agent.py` and `replies.py`
- Add data models to `src/models/` as needed
- Expand logging and error handling

## Staging Deployment

```bash
docker build . -t naijapulsebot:staging
./scripts/check_staging.sh
```

## Monetization Reporting
| Monetization Reporting | ❌ pending |

---
MIT License 