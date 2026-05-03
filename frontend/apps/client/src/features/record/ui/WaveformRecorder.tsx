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
  const rawStreamRef = useRef<MediaStream | null>(null);
  const gainRef = useRef(gain);
  gainRef.current = gain;

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

    return () => {
      record.un('record-end', handleEnd);
      try {
        record.stopRecording();
      } catch {}
      ws.destroy();
      wsRef.current = null;
      rawStreamRef.current?.getTracks().forEach((t) => t.stop());
      rawStreamRef.current = null;
      audioCtxRef.current?.close();
      audioCtxRef.current = null;
      gainNodeRef.current = null;
    };
  }, [onRecorded, mode]);

  // phase 제어
  useEffect(() => {
    const record = recordRef.current;
    if (!record) return;

    if (phase === 'finish') {
      if (record.isRecording?.() || record.isPaused?.()) {
        record.stopRecording();
      }
      rawStreamRef.current?.getTracks().forEach((t) => t.stop());
      rawStreamRef.current = null;
      audioCtxRef.current?.close();
      audioCtxRef.current = null;
      gainNodeRef.current = null;
      return;
    }

    const commands: Record<RecordingPhase, () => void> = {
      idle: () => {
        if (record.isRecording?.() || record.isPaused?.()) {
          record.stopRecording();
        }
        rawStreamRef.current?.getTracks().forEach((t) => t.stop());
        rawStreamRef.current = null;
        audioCtxRef.current?.close();
        audioCtxRef.current = null;
        gainNodeRef.current = null;
      },
      recording: () => {
        if (record.isPaused?.()) {
          record.resumeRecording();
        } else if (!record.isRecording?.()) {
          (async () => {
            const rawStream = await navigator.mediaDevices.getUserMedia({ audio: true });
            rawStreamRef.current = rawStream;

            const ctx = new AudioContext();
            audioCtxRef.current = ctx;
            const source = ctx.createMediaStreamSource(rawStream);
            const gainNode = ctx.createGain();
            gainNode.gain.value = gainRef.current;
            gainNodeRef.current = gainNode;
            const dest = ctx.createMediaStreamDestination();

            source.connect(gainNode);
            gainNode.connect(dest);

            // RecordPlugin이 내부적으로 getUserMedia를 건너뛰도록 gain-processed stream 주입
            (record as any).stream = dest.stream;
            (record as any).micStream = record.renderMicStream(dest.stream);

            await record.startRecording();
          })();
        }
      },
      paused: () => {
        if (record.isRecording?.()) {
          record.pauseRecording();
        }
      },
      finish: () => {},
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
