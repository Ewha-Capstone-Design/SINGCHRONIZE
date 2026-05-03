'use client';

import { useEffect, useState } from 'react';

const key = (jobId: string) => `rec-audio-${jobId}`;

export const saveRecordedAudio = (jobId: string, blob: Blob) => {
  const url = URL.createObjectURL(blob);
  sessionStorage.setItem(key(jobId), url);
};

export const useRecordedAudio = (jobId: string) => {
  const [src, setSrc] = useState('');

  useEffect(() => {
    const k = key(jobId);
    const stored = sessionStorage.getItem(k);
    if (stored) setSrc(stored);
    return () => {
      if (stored) URL.revokeObjectURL(stored);
      sessionStorage.removeItem(k);
    };
  }, [jobId]);

  return src;
};
