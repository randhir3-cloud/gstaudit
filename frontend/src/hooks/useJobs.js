import { useCallback, useEffect, useRef, useState } from 'react';
import { cancelJob, fetchJobs, jobsWebSocketUrl, retryJob } from '../api/jobs';

export function useJobs(sessionId) {
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(false);
  const wsRef = useRef(null);

  const refresh = useCallback(async () => {
    if (!sessionId) {
      setJobs([]);
      return;
    }
    setLoading(true);
    try {
      const data = await fetchJobs(sessionId);
      setJobs(data.jobs || []);
    } finally {
      setLoading(false);
    }
  }, [sessionId]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  useEffect(() => {
    if (!sessionId) return undefined;
    const url = jobsWebSocketUrl(sessionId);
    const ws = new WebSocket(url);
    wsRef.current = ws;
    ws.onmessage = (event) => {
      try {
        const job = JSON.parse(event.data);
        setJobs((prev) => {
          const idx = prev.findIndex((j) => j.job_id === job.job_id);
          if (idx >= 0) {
            const next = [...prev];
            next[idx] = job;
            return next;
          }
          return [job, ...prev];
        });
      } catch {
        /* ignore */
      }
    };
    ws.onclose = () => {
      setTimeout(refresh, 1000);
    };
    return () => {
      ws.close();
      wsRef.current = null;
    };
  }, [sessionId, refresh]);

  const cancel = useCallback(async (jobId) => {
    await cancelJob(jobId);
    await refresh();
  }, [refresh]);

  const retry = useCallback(async (jobId) => {
    await retryJob(jobId);
    await refresh();
  }, [refresh]);

  const grouped = {
    queued: jobs.filter((j) => j.status === 'queued' || j.status === 'retrying'),
    running: jobs.filter((j) => j.status === 'running'),
    completed: jobs.filter((j) => j.status === 'completed'),
    failed: jobs.filter((j) => ['failed', 'cancelled'].includes(j.status)),
  };

  return { jobs, grouped, loading, refresh, cancel, retry };
}

export default useJobs;
