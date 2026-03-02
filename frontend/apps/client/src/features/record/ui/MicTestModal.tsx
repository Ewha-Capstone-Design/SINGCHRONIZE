'use client';

import { useState } from 'react';
import { BaseModal } from '@/shared/components';
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
    <BaseModal
      onClose={onClose}
      className='
      relative w-full max-w-226 max-h-178 h-[80vh] rounded-20
      px-16.5 py-19.5 flex flex-col items-center justify-center
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
    </BaseModal>
  );
};

export default MicTestModal;
