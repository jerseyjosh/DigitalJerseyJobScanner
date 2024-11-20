import logging

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