# NaijaPulseBot – Living Documentation

_Last Updated: 2024-06-11_

## Table of Contents
1. [Project Overview](#project-overview)
2. [Module Responsibilities](#module-responsibilities)
3. [Feature Status](#feature-status)
4. [Outstanding Tasks / TODOs](#outstanding-tasks--todos)
5. [Next Recommended Actions](#next-recommended-actions)
6. [Configuration](#configuration)

---

## Project Overview
NaijaPulseBot is an autonomous agent that curates, summarizes, and engages with Nigerian politics & economy news. It fetches world news and X (Twitter) trends, generates content (blog + tweet threads), publishes to GitHub Pages/X, and runs an engagement bot to reply to users. The project is containerized (Docker + Compose), supports premium content, and is continuously validated via GitHub Actions CI with coverage badge automation. Monetization and observability features are being incrementally integrated.

---

## Module Responsibilities
| File / Module | Responsibility |
|---------------|----------------|
| `main.py` | Entry-point; sets up logging, schedules `run_agent_cycle()` (2h) & `run_engagement_bot()` (10min) via APScheduler. |
| `src/agent.py` | Orchestrates the main agent loop: fetches news/trends, analyzes sentiment, generates & publishes blog/thread (public & premium), updates state, logs metrics, robust error handling. |
| `src/replies.py` | Engagement bot: fetches replies, classifies them, generates & posts responses, updates state, robust error handling. |
| `src/utils.py` | Central utility module: API wrappers (news, X/Grok, OpenAI), retry/backoff, hashing, state I/O, content generators (blog/thread/premium), publishing, monetization hooks, metrics logging. Supports DRY_RUN mode for safe testing. |
| `src/twitter_api.py` | Native Twitter/X API integration using Tweepy. Provides posting, replying, fetching, and trending topic functions, decoupled from Grok. **Covered by isolated unit tests.** Supports DRY_RUN mode. |
| `src/healthcheck.py` | Docker health-check: exits non-zero if `state/state.json` is stale (>3h). |
| `src/models/` | Placeholder for future data models (currently empty). |
| `Dockerfile` & `docker-compose.yml` | Container build/runtime definitions. |
| `.github/workflows/ci.yml` | CI pipeline: lint, tests, coverage badge, Docker build, artifact upload. |
| `scripts/generate_coverage_badge.py` | Automation: generates JSON badge for test coverage. |
| `scripts/report_revenue.py` | Automation: aggregates and prints daily ROI from metrics logs. |
| `scripts/check_staging.sh` | Automation: runs app in Docker Compose and checks health. |
| `tests/` | Pytest suites covering all modules, error/retry branches, ≥80% coverage. |
| `state/state.json` | Persistent state for agent and engagement bot. |
| `logs/metrics.csv` | Metrics log for cost, tweet volume, etc. |

---

## Feature Status
| Feature | Status |
|---------|--------|
| World News fetch (`fetch_world_news`) | ✅ Implemented & Tested |
| X Trending fetch (`fetch_x_trends`) | ✅ Implemented & Tested |
| Hash/state management | ✅ Implemented & Tested |
| Blog markdown generation | ✅ Implemented |
| Blog publishing (GitPython) | ✅ Implemented |
| Tweet thread generation | ✅ Implemented |
| Post thread / reply (Grok API) | ✅ Implemented & Unit-tested |
| Engagement classification (OpenAI) | ✅ Implemented & Unit-tested |
| Docker container & healthcheck | ✅ Implemented & Tested |
| CI workflow | ✅ Lint + tests + coverage badge |
| Error Handling in run_agent_cycle | ✅ Robust, tested |
| Test coverage ≥ 80% | ✅ Achieved (including `src/twitter_api.py`) |
| Retry/Back-off for external calls | ✅ Implemented |
| Sentiment analysis integration | ✅ Implemented |
| Insider Brief Premium Feature | ✅ Implemented (stub for LLM, Stripe integration pending) |
| Staging Deployment | ✅ Implemented |
| Monetization Reporting | ⚠️ Partial (scripts exist, Stripe/Patreon integration pending) |
| Coverage Badge Automation | ✅ Implemented |
| Twitter/X Bot Integration | ✅ Decoupled from Grok; native API support via Tweepy |
| DRY_RUN Mode | ✅ Implemented for safe, non-destructive test runs |
| Observability/Logging | ⚠️ Basic logging; structured logging and external monitoring planned |

---

## Outstanding Tasks / TODOs
1. **Coverage Improvement** – Add tests for remaining error/retry branches in `src/utils.py` and new features.
2. **Secrets Management** – Switch from ENV placeholders to Docker secrets / GitHub secrets for production.
3. **Performance** – Cache trending/news data, respect rate limits, parallelize API calls if needed.
4. **Logging Enhancements** – Central structured logging, Sentry/Datadog integration.
5. **Monitoring** – Metrics export (Prometheus) & dashboards.
6. **Monetization Reporting** – Finalize Stripe/Patreon hooks and reporting; complete premium content gating.
7. **Refactor Utilities** – Split `src/utils.py` into submodules for maintainability.
8. **Configuration Management** – Centralize environment/config handling.
9. **Data Models** – Add Pydantic/dataclass models as data complexity grows.

---

## Next Recommended Actions
1. **Finalize Monetization Reporting**  
   – Complete Stripe/Patreon integration and automate revenue metrics.
2. **Secret Management Hardening**  
   – Use Docker secrets or GH encrypted secrets for production deployment.
3. **Expand Observability**  
   – Add structured logging, error tracking, and metrics export.
4. **Performance Tuning**  
   – Add caching, rate-limit handling, and parallel API calls as needed.
5. **Refactor Utilities**  
   – Modularize `src/utils.py` for clarity and maintainability.
6. **Implement Data Models**  
   – Use Pydantic/dataclasses for state and API data as needed.

---

## Configuration

- To enable native Twitter/X API support, set the following in your `.env`:
  ```dotenv
  USE_NATIVE_TWITTER=true
  TWITTER_API_KEY=your_api_key
  TWITTER_API_SECRET=your_api_secret
  TWITTER_ACCESS_TOKEN=your_access_token
  TWITTER_ACCESS_TOKEN_SECRET=your_access_token_secret
  DRY_RUN=true
  ```
- If `USE_NATIVE_TWITTER` is not set or is `false`, the bot will use Grok/X API integration as a fallback.
- If `DRY_RUN` is set to `true`, all live posting and publishing actions will be logged but not executed (safe mode for testing and CI).

**Note:** Twitter/X bot integration requires the above env vars in `.env` when using native support.

> _This document is auto-generated and should be updated after significant code changes._ 