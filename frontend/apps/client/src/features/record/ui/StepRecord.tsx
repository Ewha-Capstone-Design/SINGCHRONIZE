'use client';

import { useCallback, useEffect, useState } from 'react';
import { useModal } from '@/shared/hooks';
import RecordingControls from './RecordingControls';
import WaveformRecorder from './WaveformRecorder';
import MicTestModal from './MicTestModal';
import { useRecorder, useTimer } from '../model';
import { GUIDE_TEXT_BY_LEVEL } from '../model/constants';

// [데모] 예시 파일 경로
const DEMO_AUDIO_PATH = '/demo.m4a';

const StepRecord = ({ onNext }: { onNext: (blob: Blob) => void }) => {
  const { open: isMicTestOpen, closeModal } = useModal(true);
  const [micGain, setMicGain] = useState(1);

  const { phase, start, pause, finish } = useRecorder();
  const { mm, ss, reset, guideLevel, isMax, canDone } = useTimer(phase);

  // [데모] 실제 녹음 blob 대신 예시 파일을 fetch해서 전달
  const handleRecorded = useCallback(async () => {
    const res = await fetch(DEMO_AUDIO_PATH);
    const demoBlob = await res.blob();
    onNext(demoBlob);
  }, [onNext]);

  // 60초 도달 시 녹음 자동 종료
  useEffect(() => {
    if (isMax && phase === 'recording') {
      finish();
    }
  }, [isMax, phase, finish]);

  const guideText = GUIDE_TEXT_BY_LEVEL[guideLevel];
  const isAccent = guideLevel !== 'default';

  return (
    <>
      {/* 마이크 테스트 모달 */}
      {isMicTestOpen && (
        <MicTestModal gain={micGain} onChangeGain={setMicGain} onClose={closeModal} />
      )}

      <div className='pt-[4vh] pb-[8vh] flex flex-col gap-4 items-center justify-around max-w-xl h-full'>
        {/* 상태 문구 */}
        <div className='flex items-center h-23'>
          <p className='typo-32b text-center whitespace-pre-line'>{guideText}</p>
        </div>

        <div className='flex flex-col gap-[10] items-center w-full'>
          {/* 실시간 파형 */}
          <WaveformRecorder
            phase={phase}
            mode='record'
            gain={micGain}
            onRecorded={handleRecorded}
          />

          {/* 타이머 */}
          <p
            className={`typo-38b tabular-nums ${
              isAccent ? 'text-accent-500' : 'text-white'
            }`}
          >
            {mm}:{ss}
          </p>
        </div>

        {/* 상태별 녹음 버튼 */}
        <RecordingControls
          phase={phase}
          onStart={() => {
            if (phase === 'finish') return;
            reset();
            start();
          }}
          onPause={pause}
          onResume={() => {
            if (phase === 'finish') return;
            start();
          }}
          onDone={finish}
          canDone={canDone}
        />
      </div>
    </>
  );
};

export default StepRecord;
