'use client';

import WaveformRecorder from './WaveformRecorder';
import { IcVolumeOff, IcVolumeOn } from '@/shared/assets/icons';
import { Button } from '@singchronize/ui';
import { MIC_TEST_TEXT_BY_STATE } from '../model/constants';
import { useMicTest } from '../model/useMicTest';

type MicTestStepProps = {
  gain: number;
  onChangeGain: (v: number) => void;
  onFinish: () => void;
};

const MicTestStep = ({ gain, onChangeGain, onFinish }: MicTestStepProps) => {
  const { isTesting, levelStatus, formattedTime, startTest, stopTest } = useMicTest();

  const text = !isTesting
    ? MIC_TEST_TEXT_BY_STATE.beforeTest
    : MIC_TEST_TEXT_BY_STATE.testing[levelStatus];

  const max = 2;
  const percent = (gain / max) * 100;

  const handleFinish = () => {
    stopTest();
    onFinish();
  };

  return (
    <div className='flex flex-col items-center gap-17.5'>
      <div className='flex flex-col gap-[6] text-center'>
        <p className='typo-32b'>{text.title}</p>
        <p className='typo-20r text-gray-200'>{text.subtitle}</p>
      </div>

      <div className='flex flex-col items-center gap-[15] w-xl'>
        <WaveformRecorder
          phase={isTesting ? 'recording' : 'idle'}
          mode='test'
          gain={gain}
        />

        <span className='typo-14r text-gray-300'>{formattedTime}</span>

        <div className='w-93 flex items-center gap-3'>
          <IcVolumeOff />
          <input
            className='flex-1 mic-slider'
            type='range'
            min={0}
            max={max}
            step={0.01}
            value={gain}
            onChange={(e) => onChangeGain(Number(e.target.value))}
            style={{ '--percent': `${percent}%` } as React.CSSProperties}
          />
          <IcVolumeOn />
        </div>
      </div>

      <Button
        variant={isTesting ? 'accent' : 'normal'}
        onClick={isTesting ? handleFinish : startTest}
      >
        {isTesting ? '마이크 테스트 종료하기' : '마이크 테스트 시작하기'}
      </Button>
    </div>
  );
};

export default MicTestStep;
