import RecordingControls from './RecordingControls';
import WaveformRecorder from './WaveformRecorder';
import { useRecorder, useTimer, TITLE_BY_PHASE } from '../model';

const StepRecord = ({ onNext }: { onNext: () => void }) => {
  const { phase, start, pause, enough, handleRecorded } = useRecorder();
  const { mm, ss, reset, isMax } = useTimer(phase);

  // 30초 도달 시 종료 가능 상태 전환
  if (isMax && phase === 'recording') {
    enough();
  }

  return (
    <div className='pt-[4vh] pb-[8vh] flex flex-col gap-4 items-center justify-around max-w-xl h-full'>
      {/* 상태 문구 */}
      <div className='flex items-center h-[92]'>
        <p className='typo-32b text-center whitespace-pre-line'>
          {TITLE_BY_PHASE[phase]}
        </p>
      </div>

      <div className='flex flex-col gap-[10] items-center w-full'>
        {/* 실시간 파형 */}
        <WaveformRecorder phase={phase} onRecorded={handleRecorded} />

        {/* 타이머 */}
        <p
          className={`typo-38b tabular-nums ${phase === 'enough' ? 'text-accent-500' : 'text-white'}`}
        >
          {mm}:{ss}
        </p>
      </div>

      {/* 시작/중지/종료 버튼 */}
      <RecordingControls
        phase={phase}
        onStart={() => {
          reset();
          start();
        }}
        onPause={pause}
        onResume={start}
        onDone={onNext}
      />
    </div>
  );
};

export default StepRecord;
