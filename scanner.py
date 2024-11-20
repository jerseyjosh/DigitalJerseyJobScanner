import time
import logging
from typing import Optional, Callable, Any

import requests
from bs4 import BeautifulSoup, Tag
from tenacity import retry, wait_fixed, stop_after_attempt

from db import JobsDB
from models import JobListing, Config

logger = logging.getLogger(__name__)

class Scanner:
    """Scan digital.je for new job vacancies"""

    BASE_URL = "https://www.digital.je/digital-job-vacancies/"
    HEADERS = {
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'accept-language': 'en-US,en;q=0.9',
        'priority': 'u=0, i',
        'sec-ch-ua': '"Google Chrome";v="129", "Not=A?Brand";v="8", "Chromium";v="129"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"macOS"',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'none',
        'sec-fetch-user': '?1',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36',
    }

    def __init__(self, config: Config, new_job_callback: Optional[Callable[[JobListing], Any]] = None):
        self.config = config
        self.client = requests.Session()
        self.db = JobsDB(self.config.db_path, overwrite=self.config.overwrite_db)
        self.new_job_callback = new_job_callback

    def make_index_page_url(self, page_number: int) -> str:
        """Return the URL for a specific page number"""
        return f"{self.BASE_URL}/page/{page_number}"
    
    def make_job_page_url(self, job_id: str) -> str:
        """Return the URL for a specific job"""
        return f"{self.BASE_URL}/{job_id}"

    @retry(
            wait=wait_fixed(5), 
            stop=stop_after_attempt(3), 
            retry_error_callback=lambda x: logger.error(f"Failed to get page: {x}"),
            reraise=True
            )
    def get_page(self, url: str) -> Optional[BeautifulSoup]:
        """Get the contents of a page as soup with retry logic."""
        try:
            logger.debug(f"Getting page {url}")
            response = self.client.get(url, headers=self.HEADERS, timeout=10)
            if response.status_code == 404:
                logger.info(f"Page not found (404): {url}. Ending pagination for this cycle.")
                return None  # return None to indicate the end of pagination
            response.raise_for_status()  # raise for other HTTP errors
            return BeautifulSoup(response.text, "html.parser")
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching page {url}: {e}")
            raise  # let retry logic handle
    
    def extract_job_urls(self, page: BeautifulSoup):
        """Get links for jobs from index page soup"""
        buttons: list[Tag] = page.find_all('a', class_='btn')
        links = [button.get('href', None) for button in buttons]
        logger.debug(f"Found {len(links)} job links")
        return links
    
    def fetch_job_listing(self, job_url: str) -> JobListing:
        """Fetch job listing details"""
        page = self.get_page(job_url)
        job_title = page.find('h1').text.strip()
        table = page.find('table', class_='c-table')
        rows: list[Tag] = table.find_all('tr')
        data = {'url': job_url, 'job_title': job_title}
        for row in rows:
            key = row.find('td').text.strip().strip(':').lower().replace(' ', '_')
            value_cell: Tag = row.find_all('td')[1]
            value = value_cell.get_text(strip=True)
            data[key] = value

        # create object
        job_listing = JobListing(
            url=data['url'],
            job_title=data['job_title'],
            company_name=data.get('company_name'),
            contract_type=data.get('contract_type'),
            role_type=data.get('role_type'),
            employment_type=data.get('employment_type'),
            contact=data.get('contact'),
            closing_date=data.get('closing_date'),
        )

        return job_listing
    
    def run_once(self):
        """Run through all pages once"""
        page_number = 1
        page_has_contents = True
        while page_has_contents:
            page_url = self.make_index_page_url(page_number)
            page = self.get_page(page_url)
            if page is None:
                break
            job_urls = self.extract_job_urls(page)
            if len(job_urls) == 0:
                page_has_contents = False
            else:
                for job_url in job_urls:
                    job_listing = self.fetch_job_listing(job_url)
                    is_new_job_listing = self.db.insert_job(job_listing)
                    if is_new_job_listing:
                        self.new_job_callback(job_listing)
            page_number += 1
    
    def run_forever(self):
        """Run the scanner indefinitely"""
        logger.debug(f"Scanner starting")
        try:
            while True:
                self.run_once()
                logger.info(f"Sleeping for {self.config.scan_interval_minutes} minutes")
                time.sleep(int(self.config.scan_interval_minutes) * 60)
        except KeyboardInterrupt:
            logger.info("Scanner interrupted, stopping")
            return

    