import { useEffect, useRef, useState } from 'react';
import { api } from '../services/api';

export function useTaskPoller(taskId, { intervalMs = 3000, onComplete, onFailed } = {}) {
  const [status, setStatus] = useState(null);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  const onCompleteRef = useRef(onComplete);
  const onFailedRef = useRef(onFailed);

  useEffect(() => {
    onCompleteRef.current = onComplete;
    onFailedRef.current = onFailed;
  }, [onComplete, onFailed]);

  useEffect(() => {
    if (!taskId) {
      // No active task — clear any leftover status so consumers don't read a
      // stale 'pending'/'processing' from a previous task.
      setStatus(null);
      setResult(null);
      setError(null);
      setLoading(false);
      return undefined;
    }

    let stopped = false;
    let timeoutId = null;

    const stop = () => {
      stopped = true;
      if (timeoutId) clearTimeout(timeoutId);
    };

    const poll = async () => {
      if (stopped) return;

      try {
        setLoading(true);
        const res = await api.getTaskStatus(taskId);

        if (stopped) return;

        if (!res.success) {
          setError(res.msg);
          onFailedRef.current?.(res.msg);
          stop();
          return;
        }

        const task = res.data;
        setStatus(task.status);

        if (task.status === 'completed') {
          setResult(task.result);
          onCompleteRef.current?.(task.result);
          stop();
          return;
        }

        if (task.status === 'failed') {
          const msg = task.error_message || 'Task failed';
          setError(msg);
          onFailedRef.current?.(msg);
          stop();
          return;
        }
      } catch (e) {
        if (!stopped) {
          setError(e.message);
          onFailedRef.current?.(e.message);
          stop();
        }
        return;
      } finally {
        if (!stopped) setLoading(false);
      }

      if (!stopped) {
        timeoutId = setTimeout(poll, intervalMs);
      }
    };

    setStatus(null);
    setResult(null);
    setError(null);
    poll();

    return stop;
  }, [taskId, intervalMs]);

  return { status, result, error, loading };
}
