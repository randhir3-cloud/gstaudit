"""Background job worker — polls queue and executes jobs concurrently."""

from __future__ import annotations

import threading
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Optional, Set

from config.settings import get_settings
from jobs.executors import safe_execute
from models.job import JobStatus
from repositories.job_repository import get_job_repository
from services.job_service import mark_running


class JobWorker:
    def __init__(self, worker_count: Optional[int] = None) -> None:
        settings = get_settings()
        self._worker_count = worker_count or settings.job_worker_count
        self._poll_interval = settings.job_poll_interval_ms / 1000.0
        self._executor: Optional[ThreadPoolExecutor] = None
        self._poll_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._active: Set[str] = set()
        self._active_lock = threading.Lock()

    def start(self) -> None:
        if self._poll_thread and self._poll_thread.is_alive():
            return
        self._stop_event.clear()
        self._executor = ThreadPoolExecutor(max_workers=self._worker_count, thread_name_prefix="gais-job")
        self._poll_thread = threading.Thread(target=self._poll_loop, name="gais-job-poller", daemon=True)
        self._poll_thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        if self._poll_thread:
            self._poll_thread.join(timeout=5)
        if self._executor:
            self._executor.shutdown(wait=False, cancel_futures=True)
        self._executor = None

    def _poll_loop(self) -> None:
        repo = get_job_repository()
        while not self._stop_event.is_set():
            with self._active_lock:
                active_count = len(self._active)
            if active_count >= self._worker_count:
                time.sleep(self._poll_interval)
                continue

            job = repo.claim_next_queued()
            if not job:
                time.sleep(self._poll_interval)
                continue

            job = mark_running(job)
            with self._active_lock:
                self._active.add(job.job_id)

            assert self._executor is not None

            def _run(jid: str = job.job_id) -> None:
                try:
                    current = repo.get_by_id(jid)
                    if current and current.status != JobStatus.CANCELLED:
                        safe_execute(current)
                finally:
                    with self._active_lock:
                        self._active.discard(jid)

            self._executor.submit(_run)


_worker: Optional[JobWorker] = None


def start_worker() -> JobWorker:
    global _worker
    if _worker is None:
        _worker = JobWorker()
        _worker.start()
    return _worker


def stop_worker() -> None:
    global _worker
    if _worker:
        _worker.stop()
        _worker = None
