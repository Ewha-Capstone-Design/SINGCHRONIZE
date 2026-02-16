'use client';

import { useState } from 'react';
import { IcClose } from '@/shared/assets/icons';
import MicTestStep from './MicTestStep';
import StartAnalysisStep from './StartAnalysisStep';

type MicTestModalProps = {
  gain: number;
  onChangeGain: (v: number) => void;
  onClose: () => void;
};

type Step = 'mic-test' | 'start-analysis';

const MicTestModal = ({ gain, onChangeGain, onClose }: MicTestModalProps) => {
  const [step, setStep] = useState<Step>('mic-test');

  return (
    <div className='fixed inset-0 z-50 flex items-center justify-center bg-dim'>
      <div
        className='
        relative w-full max-w-226 h-178 rounded-20
        px-16 py-20 flex flex-col items-center justify-center gap-10
        bg-bg bg-[radial-gradient(50%_50%_at_50%_50%,rgba(200,255,0,0.17)_0%,rgba(22,22,22,0.17)_100%)]
        bg-size-[130%_200%]
        bg-position-[50%_-10%]
        '
      >
        {step === 'mic-test' && (
          <MicTestStep
            gain={gain}
            onChangeGain={onChangeGain}
            onFinish={() => setStep('start-analysis')}
          />
        )}

        {step === 'start-analysis' && (
          <StartAnalysisStep
            onStart={() => {
              onClose();
            }}
          />
        )}

        <button className='absolute bottom-[-64]' onClick={onClose}>
          <IcClose />
        </button>
      </div>
    </div>
  );
};

export default MicTestModal;
