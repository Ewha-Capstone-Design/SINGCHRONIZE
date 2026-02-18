import { useEffect, useMemo, useState } from 'react';
import { RecordingPhase } from '@/shared/types/recommend';
import {
  MAX_RECORD_SECONDS,
  RECORD_GUIDE_THRESHOLDS,
  RecordGuideLevel,
} from './constants';

export const useTimer = (phase: RecordingPhase) => {
  const [seconds, setSeconds] = useState(0);

  useEffect(() => {
    if (phase !== 'recording') return;

    const id = setInterval(() => {
      setSeconds((s) => Math.min(s + 1, MAX_RECORD_SECONDS));
    }, 1000);

    return () => clearInterval(id);
  }, [phase]);

  const reset = () => setSeconds(0);

  const guideLevel = useMemo<RecordGuideLevel>(() => {
    if (seconds >= RECORD_GUIDE_THRESHOLDS.WARNING) return 'warning'; // 50초 이상
    if (seconds >= RECORD_GUIDE_THRESHOLDS.ENOUGH) return 'enough'; // 35초 이상
    return 'default'; // 35초 미만
  }, [seconds]);

  const mm = String(Math.floor(seconds / 60)).padStart(2, '0');
  const ss = String(seconds % 60).padStart(2, '0');

  const isMax = seconds >= MAX_RECORD_SECONDS; // 60초 도달
  const canDone = seconds >= RECORD_GUIDE_THRESHOLDS.ENOUGH; // 35초 이상만 종료 가능

  return {
    seconds,
    mm,
    ss,
    reset,
    guideLevel,
    isMax,
    canDone,
  };
};
