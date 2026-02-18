import { useCallback, useState } from 'react';
import { RecordingPhase } from '@/shared/types/recommend';

export const useRecorder = () => {
  const [phase, setPhase] = useState<RecordingPhase>('idle');
  const [lastBlob, setLastBlob] = useState<Blob | null>(null);

  const start = useCallback(() => {
    setPhase('recording');
  }, []);

  const pause = useCallback(() => {
    setPhase('paused');
  }, []);

  const finish = useCallback(() => {
    setPhase('finish');
  }, []);

  const handleRecorded = useCallback((blob: Blob) => {
    setLastBlob(blob);
  }, []);

  return {
    phase,
    setPhase,
    start,
    pause,
    finish,
    handleRecorded,
    lastBlob,
  };
};
