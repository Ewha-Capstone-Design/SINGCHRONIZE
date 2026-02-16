'use client';

import { useEffect, useRef, useState } from 'react';
import WaveformRecorder from './WaveformRecorder';
import { IcVolumeOff, IcVolumeOn } from '@/shared/assets/icons';
import { Button } from '@singchronize/ui';

type MicTestStepProps = {
  gain: number;
  onChangeGain: (v: number) => void;
  onFinish: () => void;
};

type LevelStatus = 'low' | 'ok' | 'high';

const MicTestStep = ({ gain, onChangeGain, onFinish }: MicTestStepProps) => {
  const [stream, setStream] = useState<MediaStream | null>(null);
  const [levelStatus, setLevelStatus] = useState<LevelStatus>('low');
  const rafRef = useRef<number | null>(null);

  const requestMic = async () => {
    try {
      const s = await navigator.mediaDevices.getUserMedia({ audio: true });
      setStream(s);
    } catch (e) {
      console.error('마이크 권한 획득 실패: ', e);
      setStream(null);
    }
  };

  useEffect(() => {
    if (!stream) return;

    const ctx = new AudioContext();
    const source = ctx.createMediaStreamSource(stream);
    const analyser = ctx.createAnalyser();
    analyser.fftSize = 2048;
    source.connect(analyser);

    const data = new Uint8Array(analyser.fftSize);

    const tick = () => {
      analyser.getByteTimeDomainData(data);

      let sum = 0;
      for (const raw of data) {
        const v = (raw - 128) / 128;
        sum += v * v;
      }
      const rms = Math.sqrt(sum / data.length);

      if (rms < 0.01) setLevelStatus('low');
      else if (rms > 0.15) setLevelStatus('high');
      else setLevelStatus('ok');

      rafRef.current = requestAnimationFrame(tick);
    };

    tick();

    return () => {
      if (rafRef.current) cancelAnimationFrame(rafRef.current);
      source.disconnect();
      ctx.close();
    };
  }, [stream]);

  const handleFinish = () => {
    if (stream) stream.getTracks().forEach((t) => t.stop());
    setStream(null);
    onFinish();
  };

  const isTesting = !!stream;

  const titleText = !isTesting
    ? '마이크 테스트 먼저 해볼까요?'
    : levelStatus === 'high'
      ? '소리가 크게 들려요'
      : levelStatus === 'low'
        ? '소리가 작게 들려요'
        : '소리가 적절하게 들려요';

  const subtitleText = !isTesting
    ? '시작하기를 눌러 진행해 주세요!'
    : levelStatus === 'high'
      ? '볼륨을 조금 낮춰 주세요!'
      : levelStatus === 'low'
        ? '볼륨을 조금 높여 주세요!'
        : '지금 상태를 유지해 주세요!';

  const max = 2;
  const percent = (gain / max) * 100;

  return (
    <>
      <div className='text-center'>
        <p className='typo-32b'>{titleText}</p>
        <p className='typo-20r text-gray-200 mt-[6]'>{subtitleText}</p>
      </div>

      <WaveformRecorder phase={stream ? 'recording' : 'idle'} mode='test' gain={gain} />

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

      <Button
        variant={isTesting ? 'accent' : 'normal'}
        onClick={isTesting ? handleFinish : requestMic}
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
    </>
  );
};

export default MicTestStep;
