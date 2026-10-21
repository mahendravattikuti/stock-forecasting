/**
 * useFetch Hook
 * Generic hook for fetching data with caching and error handling
 */

import { useState, useEffect, useRef, useCallback } from 'react';

export function useFetch(fetchFn, dependencies = [], options = {}) {
  const {
    onSuccess = null,
    onError = null,
    retryCount = 3,
    retryDelay = 1000,
    cacheTime = 0, // in milliseconds, 0 = no cache
  } = options;

  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const retriesRef = useRef(0);
  const cacheRef = useRef({ data: null, timestamp: 0 });

  const execute = useCallback(async () => {
    // Check cache
    const now = Date.now();
    if (
      cacheTime > 0 &&
      cacheRef.current.data &&
      now - cacheRef.current.timestamp < cacheTime
    ) {
      setData(cacheRef.current.data);
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const result = await fetchFn();
      setData(result);
      
      // Cache result
      cacheRef.current = { data: result, timestamp: now };
      
      if (onSuccess) onSuccess(result);
      retriesRef.current = 0;
    } catch (err) {
      // Retry logic
      if (retriesRef.current < retryCount) {
        retriesRef.current += 1;
        setTimeout(() => execute(), retryDelay);
      } else {
        setError(err);
        if (onError) onError(err);
      }
    } finally {
      setLoading(false);
    }
  }, [fetchFn, onSuccess, onError, retryCount, retryDelay, cacheTime]);

  useEffect(() => {
    execute();
  }, dependencies);

  const retry = useCallback(() => {
    retriesRef.current = 0;
    execute();
  }, [execute]);

  const refetch = useCallback(() => {
    cacheRef.current = { data: null, timestamp: 0 };
    execute();
  }, [execute]);

  return { data, loading, error, retry, refetch, execute };
}

export default useFetch;
