import logging
import sqlite3
from contextlib import contextmanager
from typing import Optional, List
from models import JobListing

logger = logging.getLogger(__name__)


class JobsDB:
    def __init__(self, db_path: str, overwrite: bool = False):
        logger.debug(f"Connecting to database at {db_path}")
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row  # Enables fetching rows as dictionaries
        self.cursor = self.conn.cursor()
        self.create_table(overwrite)

    def create_table(self, overwrite):
        """
        Create the jobs table. If overwrite is True, drop the existing table and recreate it.
        """
        if overwrite:
            logger.debug("Dropping existing jobs table")
            self.cursor.execute("DROP TABLE IF EXISTS jobs")
        
        logger.debug("Creating table jobs")
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS jobs (
                id INTEGER PRIMARY KEY,
                url TEXT NOT NULL UNIQUE,
                job_title TEXT,
                company_name TEXT,
                contract_type TEXT,
                role_type TEXT,
                employment_type TEXT,
                contact TEXT,
                closing_date TEXT
            )
            """
        )
        self.conn.commit()


    def insert_job(self, job_listing: JobListing) -> Optional[int]:
        """Insert job listing into database. Returns the inserted job's ID or None if it exists."""
        if not self.job_exists(job_listing.url):
            logger.debug(f"Inserting job {job_listing.url}")
            with self.transaction():
                self.cursor.execute(
                    """
                    INSERT INTO jobs (url, job_title, company_name, contract_type, role_type, employment_type, contact, closing_date)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    job_listing.to_tuple(),
                )
                return self.cursor.lastrowid
        else:
            logger.debug(f"Job {job_listing.url} already exists")
            return None

    def job_exists(self, url: str) -> bool:
        self.cursor.execute("SELECT 1 FROM jobs WHERE url = ?", (url,))
        return self.cursor.fetchone() is not None

    def get_job_by_url(self, url: str) -> Optional[JobListing]:
        """Retrieve a job listing by URL."""
        self.cursor.execute("SELECT * FROM jobs WHERE url = ?", (url,))
        row = self.cursor.fetchone()
        return JobListing.from_dict(dict(row)) if row else None

    def get_all_jobs(self) -> List[JobListing]:
        """Retrieve all job listings."""
        self.cursor.execute("SELECT * FROM jobs")
        rows = self.cursor.fetchall()
        return [JobListing.from_dict(dict(row)) for row in rows]

    @contextmanager
    def transaction(self):
        """Context manager for database transactions."""
        try:
            yield
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Transaction failed: {e}")
            raise

    def close(self):
        """Close the database connection."""
        logger.debug("Closing database connection")
        self.conn.close()
