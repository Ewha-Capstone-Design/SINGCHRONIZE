'use client';

import { useEffect, useRef } from 'react';
import WaveSurfer from 'wavesurfer.js';
import RecordPlugin from 'wavesurfer.js/dist/plugins/record.js';
import { RecordingPhase } from '@/shared/types/recommend';

type WaveformRecorderProps = {
  phase: RecordingPhase;
  onRecorded?: (blob: Blob) => void;
};

const WaveformRecorder = ({ phase, onRecorded }: WaveformRecorderProps) => {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const wsRef = useRef<WaveSurfer | null>(null);
  const recordRef = useRef<any>(null);

  useEffect(() => {
    if (!containerRef.current) return;

    const record = RecordPlugin.create({
      renderRecordedAudio: false,
      scrollingWaveform: true,
    });
    recordRef.current = record;

    const ws = WaveSurfer.create({
      container: containerRef.current,
      height: 150,
      waveColor: '#c8ff00',
      cursorWidth: 0,
      interact: false,
      normalize: true,
      autoCenter: true,
      barWidth: 2,
      barGap: 2,
      plugins: [record],
    });

    wsRef.current = ws;

    const handleEnd = (blob: Blob) => {
      onRecorded?.(blob);
    };

    record.on('record-end', handleEnd);

    return () => {
      record.un('record-end', handleEnd);
      try {
        record.stopRecording();
      } catch {}
      ws.destroy();
      wsRef.current = null;
    };
  }, [onRecorded]);

  useEffect(() => {
    const record = recordRef.current;
    if (!record) return;

    if (phase === 'recording') {
      record.startRecording();
    } else if (phase === 'paused') {
      record.pauseRecording();
    }
  }, [phase]);

  return (
    <div className='relative w-full h-[150] flex items-center'>
      {/* 왼쪽 파형 영역 */}
      <div className='w-1/2 h-full overflow-hidden'>
        <div ref={containerRef} className='w-full h-full' />
      </div>

      {/* 중앙 고정 커서 */}
      <div className='pointer-events-none absolute left-1/2 -translate-x-1/2 flex flex-col items-center'>
        <div className='w-2 h-2 rounded-full bg-brand' />
        <div className='w-[2] h-[150] bg-brand' />
      </div>
    </div>
  );
};

export default WaveformRecorder;
