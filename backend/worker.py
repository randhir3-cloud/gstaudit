#!/usr/bin/env python3
"""Standalone GAIS background job worker."""

from jobs.worker import JobWorker

if __name__ == "__main__":
    worker = JobWorker()
    worker.start()
    print("GAIS job worker running. Press Ctrl+C to stop.")
    try:
        import time
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        worker.stop()
        print("Worker stopped.")
