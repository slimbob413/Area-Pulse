"""
main.py

Entry point for NaijaPulseBot. Schedules agent and engagement bot jobs.

- Schedules run_agent_cycle() every 2 hours.
- Schedules run_engagement_bot() every 10 minutes.
- Sets up logging to logs/agent.log.
"""

from dotenv import load_dotenv; load_dotenv()
import logging
import os
from apscheduler.schedulers.blocking import BlockingScheduler
from src.agent import run_agent_cycle
from src.replies import run_engagement_bot

# Configure logging
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    filename='logs/agent.log',
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s'
)
logging.getLogger().addHandler(logging.StreamHandler())

ENABLE_ENGAGEMENT_BOT = os.getenv("ENABLE_ENGAGEMENT_BOT", "true").lower() == "true"

scheduler = BlockingScheduler()

scheduler.add_job(run_agent_cycle, 'interval', minutes=10, id='agent_cycle')
if ENABLE_ENGAGEMENT_BOT:
    scheduler.add_job(run_engagement_bot, 'interval', minutes=10, id='engagement_bot')
else:
    logging.info("Engagement bot scheduling is disabled via ENABLE_ENGAGEMENT_BOT=false")

if __name__ == "__main__":
    logging.info("Starting NaijaPulseBot scheduler...")
    try:
        run_agent_cycle()
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logging.info("Scheduler stopped.") 