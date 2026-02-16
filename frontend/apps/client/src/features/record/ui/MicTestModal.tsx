'use client';

import { useEffect, useRef, useState } from 'react';
import WaveformRecorder from './WaveformRecorder';
import { IcClose, IcVolumeOff, IcVolumeOn } from '@/shared/assets/icons';
import { Button } from '@singchronize/ui';

type MicTestModalProps = {
  gain: number;
  onChangeGain: (v: number) => void;
  onClose: () => void;
};

type LevelStatus = 'low' | 'ok' | 'high';

const MicTestModal = ({ gain, onChangeGain, onClose }: MicTestModalProps) => {
  const [stream, setStream] = useState<MediaStream | null>(null);
  const [levelStatus, setLevelStatus] = useState<LevelStatus>('low');

  const rafRef = useRef<number | null>(null);

  // 마이크 권한 요청 & 마이크 테스트 시작
  const requestMic = async () => {
    try {
      const s = await navigator.mediaDevices.getUserMedia({ audio: true });
      setStream(s);
    } catch (e) {
      console.error('마이크 권한 획득 실패: ', e);
      setStream(null);
    }
  };

  // AudioContext + Analyser 연결해서 RMS로 레벨 판정
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

      const LOW_THRESHOLD = 0.01;
      const HIGH_THRESHOLD = 0.15;

      if (rms < LOW_THRESHOLD) {
        setLevelStatus('low');
      } else if (rms > HIGH_THRESHOLD) {
        setLevelStatus('high');
      } else {
        setLevelStatus('ok');
      }

      rafRef.current = requestAnimationFrame(tick);
    };

    tick();

    return () => {
      if (rafRef.current) cancelAnimationFrame(rafRef.current);
      source.disconnect();
      ctx.close();
    };
  }, [stream]);

  // 테스트 종료 + 모달 닫기
  const handleClose = () => {
    if (stream) {
      stream.getTracks().forEach((t) => t.stop());
    }
    onClose();
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
    <div className='fixed inset-0 z-50 flex items-center justify-center bg-dim'>
      <div
        className='relative w-full max-w-226 rounded-20 px-16 py-20 flex flex-col items-center gap-10
        bg-bg bg-[radial-gradient(50%_50%_at_50%_50%,rgba(200,255,0,0.17)_0%,rgba(22,22,22,0.17)_100%)] bg-size-[150%_170%] bg-position-[50%_-30%]'
      >
        <div className='text-center'>
          <p className='typo-32b'>{titleText}</p>
          <p className='typo-20r text-gray-200 mt-[6]'>{subtitleText}</p>
        </div>

        {/* 테스트 파형 */}
        <WaveformRecorder phase={stream ? 'recording' : 'idle'} mode='test' gain={gain} />

        {/* 음량 조절 슬라이더 */}
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

        {/* 테스트 시작하기 / 완료하기 버튼 */}
        <Button
          variant={stream ? 'accent' : 'normal'}
          onClick={stream ? handleClose : requestMic}
        >
          {stream ? '마이크 테스트 종료하기' : '마이크 테스트 시작하기'}
        </Button>

        {/* 테스트 안내사항 */}
        <div className='flex flex-col items-center gap-6 w-full'>
          <div className='w-full h-[1] bg-gray-700' />
          <div className='flex gap-12 typo-16r'>
            <p>안내사항</p>
            <ul className='flex flex-col gap-1 list-disc'>
              <li>마이크에 대고 말을 해주세요!</li>
              <li>
                음량이 너무 작으면 분석 정확도가 낮아질 수 있으며, 너무 크면 소리가 왜곡될
                수 있어요!
              </li>
            </ul>
          </div>
        </div>

        <button className='absolute bottom-[-64]' onClick={handleClose}>
          <IcClose />
        </button>
      </div>
    </div>
  );
};

export default MicTestModal;
