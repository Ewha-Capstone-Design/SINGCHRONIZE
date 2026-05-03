import { useEffect, useRef, useState } from 'react';
import { formatTime } from '@/shared/lib/formatTime';
import { LevelStatus } from './constants';

export const useMicTest = (gain: number) => {
  const [stream, setStream] = useState<MediaStream | null>(null);
  const [levelStatus, setLevelStatus] = useState<LevelStatus>('low');
  const [elapsedTime, setElapsedTime] = useState(0);
  const rafRef = useRef<number | null>(null);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const gainNodeRef = useRef<GainNode | null>(null);

  const isTesting = !!stream;

  const startTest = async () => {
    try {
      const s = await navigator.mediaDevices.getUserMedia({ audio: true });
      setStream(s);
      setElapsedTime(0);
    } catch (e) {
      console.error('마이크 권한 획득 실패: ', e);
      setStream(null);
    }
  };

  const stopTest = () => {
    if (stream) stream.getTracks().forEach((t) => t.stop());
    setStream(null);
    setElapsedTime(0);
    if (timerRef.current) clearInterval(timerRef.current);
    if (rafRef.current) cancelAnimationFrame(rafRef.current);
  };

  useEffect(() => {
    if (!stream) return;

    timerRef.current = setInterval(() => {
      setElapsedTime((prev) => prev + 1);
    }, 1000);

    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [stream]);

  useEffect(() => {
    if (!stream) return;

    const ctx = new AudioContext();
    const source = ctx.createMediaStreamSource(stream);
    const gainNode = ctx.createGain();
    gainNode.gain.value = gain;
    gainNodeRef.current = gainNode;
    const analyser = ctx.createAnalyser();
    analyser.fftSize = 2048;
    source.connect(gainNode);
    gainNode.connect(analyser);

    const data = new Uint8Array(analyser.fftSize);

    const tick = () => {
      analyser.getByteTimeDomainData(data);

      let sum = 0;
      for (const raw of data) {
        const v = (raw - 128) / 128;
        sum += v * v;
      }
      const rms = Math.sqrt(sum / data.length);

      if (rms < 0.01) setLevelStatus('low');
      else if (rms > 0.15) setLevelStatus('high');
      else setLevelStatus('ok');

      rafRef.current = requestAnimationFrame(tick);
    };

    tick();

    return () => {
      if (rafRef.current) cancelAnimationFrame(rafRef.current);
      gainNodeRef.current = null;
      source.disconnect();
      gainNode.disconnect();
      ctx.close();
    };
  }, [stream]);

  // gain 변경 시 analyser 체인에 반영
  useEffect(() => {
    if (gainNodeRef.current) {
      gainNodeRef.current.gain.value = gain;
    }
  }, [gain]);

  const { formatted } = formatTime(elapsedTime);

  return {
    isTesting,
    levelStatus,
    formattedTime: formatted,
    startTest,
    stopTest,
  };
};
