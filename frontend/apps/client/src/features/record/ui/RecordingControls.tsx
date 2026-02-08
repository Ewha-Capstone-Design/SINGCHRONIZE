import RecordingButton from './RecordingButton';
import { RecordingPhase } from '@/shared/types/recommend';

type RecordingControlsProps = {
  phase: RecordingPhase;
  onStart: () => void;
  onPause: () => void;
  onResume: () => void;
  onDone: () => void;
};

const RecordingControls = ({
  phase,
  onStart,
  onPause,
  onResume,
  onDone,
}: RecordingControlsProps) => {
  if (phase === 'idle') {
    return (
      <div className='flex items-center justify-center'>
        <RecordingButton variant='start' onClick={onStart} />
      </div>
    );
  }

  if (phase === 'recording') {
    return (
      <div className='flex items-center justify-center gap-4'>
        <RecordingButton variant='pause' onClick={onPause} />
        <RecordingButton variant='done' onClick={onDone} />
      </div>
    );
  }

  // paused
  return (
    <div className='flex items-center justify-center gap-4'>
      <RecordingButton variant='start' onClick={onResume} />
      <RecordingButton variant='done' onClick={onDone} />
    </div>
  );
};

export default RecordingControls;
