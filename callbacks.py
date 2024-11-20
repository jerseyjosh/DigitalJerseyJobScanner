import logging
from typing import List

from models import JobListing

logger = logging.getLogger(__name__)

def on_new_job(job_listing: JobListing):
    """What to do when new job is found listed."""
    logger.info(f"Callback for: {job_listing}")

def check_python_job(job_listing: JobListing):
    """Check if job is python related"""
    job_string = str(job_listing.to_tuple())
    if 'python' in job_string.lower():
        logger.info(f"Python job found: {job_listing}")

def _lazy_telegram_credentials() -> tuple[str, str]:
    import os
    from dotenv import load_dotenv, find_dotenv
    load_dotenv(find_dotenv())
    key = os.getenv("TELEGRAM_KEY") or os.environ.get("TELEGRAM_KEY")
    chat_id = os.getenv("TELEGRAM_CHAT_ID") or os.environ.get("TELEGRAM_CHAT_ID")
    if not key or not chat_id:
        raise ValueError("Telegram credentials not found in environment variables.")
    return key, chat_id

def telegram_alert(job_listing: JobListing):
    """Send a Telegram alert when a new job is found."""
    # ----
    # lazy telegram integration
    import requests
    KEY, ID = _lazy_telegram_credentials()
    message = f"New Job Alert:\nTitle: {job_listing.job_title}\nCompany: {job_listing.company_name}\nURL: {job_listing.url}"
    url = f"https://api.telegram.org/bot{KEY}/sendMessage"
    payload = {"chat_id": ID, "text": message}
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()  # Raise an exception for HTTP errors
        logger.info("Telegram alert sent successfully.")
    except requests.RequestException as e:
        logger.error(f"Failed to send Telegram alert: {e}")
    # ----

def telegram_alert_on_contains_words(job_listing: JobListing):
    """Check if job listing contains any of the words and then alert"""
    # check job listing
    WORDS = ["python", "developer", "engineer", "software", "django", "flask", "fastapi", "backend", "fullstack"]
    job_string = str(job_listing.to_tuple())
    if any(word in job_string.lower() for word in WORDS):
            logger.info(f"Job found with keywords: {job_listing}")
            # ----
            # lazy telegram integration
            import requests
            KEY, ID = _lazy_telegram_credentials()
            message = f"New Job Alert:\nTitle: {job_listing.job_title}\nCompany: {job_listing.company_name}\nURL: {job_listing.url}"
            url = f"https://api.telegram.org/bot{KEY}/sendMessage"
            payload = {"chat_id": ID, "text": message}
            try:
                response = requests.post(url, json=payload)
                response.raise_for_status()  # Raise an exception for HTTP errors
                logger.info("Telegram alert sent successfully.")
            except requests.RequestException as e:
                logger.error(f"Failed to send Telegram alert: {e}")
            # ----
    