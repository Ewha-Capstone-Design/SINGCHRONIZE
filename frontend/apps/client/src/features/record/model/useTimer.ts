import { useEffect, useState } from 'react';
import { RecordingPhase } from '@/shared/types/recommend';
import { MAX_RECORD_SECONDS } from './constants';

export const useTimer = (phase: RecordingPhase) => {
  const [seconds, setSeconds] = useState(0);

  useEffect(() => {
    if (phase !== 'recording') return;

    const id = setInterval(() => {
      setSeconds((s) => {
        const next = s + 1;
        if (next >= MAX_RECORD_SECONDS) {
          return MAX_RECORD_SECONDS;
        }
        return next;
      });
    }, 1000);

    return () => clearInterval(id);
  }, [phase]);

  const reset = () => setSeconds(0);

  const mm = String(Math.floor(seconds / 60)).padStart(2, '0');
  const ss = String(seconds % 60).padStart(2, '0');

  return {
    seconds,
    mm,
    ss,
    reset,
    isMax: seconds >= MAX_RECORD_SECONDS,
  };
};
