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
  const { isTesting, levelStatus, startTest, stopTest } = useMicTest();

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
    <div className='flex flex-col items-center gap-[42]'>
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

        <div className='w-[372] flex items-center gap-3'>
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

      <div className='flex flex-col items-center gap-6 w-full'>
        <div className='w-full h-[1] bg-gray-700' />
        <div className='flex gap-12 typo-16r'>
          <p>안내사항</p>
          <ul className='flex flex-col gap-1'>
            <li>∙ 마이크에 대고 말을 해주세요!</li>
            <li>
              ∙ 음량이 너무 작으면 분석 정확도가 낮아질 수 있으며, 너무 크면 소리가 왜곡될
              수 있어요!
            </li>
          </ul>
        </div>
      </div>
    </div>
  );
};

export default MicTestStep;
