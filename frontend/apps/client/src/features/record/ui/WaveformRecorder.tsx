'use client';

import { useEffect, useRef } from 'react';
import WaveSurfer from 'wavesurfer.js';
import RecordPlugin from 'wavesurfer.js/dist/plugins/record.js';
import { RecordingPhase } from '@/shared/types/recommend';

type WaveformRecorderProps = {
  phase: RecordingPhase;
  mode?: 'test' | 'record';
  gain?: number;
  onRecorded?: (blob: Blob) => void;
};

const WaveformRecorder = ({
  phase,
  onRecorded,
  mode = 'record',
  gain = 1,
}: WaveformRecorderProps) => {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const wsRef = useRef<WaveSurfer | null>(null);
  const recordRef = useRef<any>(null);
  const gainNodeRef = useRef<GainNode | null>(null);
  const audioCtxRef = useRef<AudioContext | null>(null);

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
      if (mode === 'record') {
        onRecorded?.(blob);
      }
    };

    record.on('record-end', handleEnd);

    // AudioContext + GainNode 준비 (앱 내부 레벨 조절용)
    const ctx = new AudioContext();
    audioCtxRef.current = ctx;
    const gainNode = ctx.createGain();
    gainNode.gain.value = gain;
    gainNodeRef.current = gainNode;

    return () => {
      record.un('record-end', handleEnd);
      try {
        record.stopRecording();
      } catch {}
      ws.destroy();
      wsRef.current = null;
      ctx.close();
    };
  }, [onRecorded, mode]);

  // phase 제어
  useEffect(() => {
    const record = recordRef.current;
    if (!record) return;

    if (phase === 'finish') {
      const isActive = record.isRecording?.() || record.isPaused?.();
      if (isActive) {
        record.stopRecording();
      }
      return;
    }

    const commands: Record<RecordingPhase, () => void> = {
      idle: () => {
        // 아무 것도 하지 않음
      },
      recording: () => {
        if (record.isPaused && record.isPaused()) {
          record.resumeRecording();
        } else if (!record.isRecording || !record.isRecording()) {
          record.startRecording();
        }
      },
      paused: () => {
        if (record.isRecording && record.isRecording()) {
          record.pauseRecording();
        }
      },
      finish: () => {
        // 위에서 이미 처리
      },
    };

    commands[phase]?.();
  }, [phase]);

  // gain 반영
  useEffect(() => {
    if (gainNodeRef.current) {
      gainNodeRef.current.gain.value = gain;
    }
  }, [gain]);

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
