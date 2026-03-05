'use client';

import { useEffect, useMemo, useRef, useState } from 'react';
import { IcDownload, IcPause, IcPlay } from '../assets/icons';
import { cn } from '../lib/cn';

type AudioPlayerProps = {
  src: string;
  className?: string;
};

const AudioPlayer = ({ src, className }: AudioPlayerProps) => {
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const barRef = useRef<HTMLDivElement | null>(null);
  const rafRef = useRef<number | null>(null);

  const [isPlaying, setIsPlaying] = useState(false);
  const [duration, setDuration] = useState(0);
  const [currentTime, setCurrentTime] = useState(0);

  const progress = useMemo(() => {
    if (duration <= 0) return 0;
    const v = currentTime / duration;
    return Math.min(1, Math.max(0, v));
  }, [currentTime, duration]);

  const stopRaf = () => {
    if (rafRef.current === null) return;
    cancelAnimationFrame(rafRef.current);
    rafRef.current = null;
  };

  const startRaf = () => {
    stopRaf();

    const tick = () => {
      const audio = audioRef.current;
      if (!audio) return;

      setCurrentTime(audio.currentTime);

      if (!audio.paused && !audio.ended) {
        rafRef.current = requestAnimationFrame(tick);
      } else {
        rafRef.current = null;
      }
    };

    rafRef.current = requestAnimationFrame(tick);
  };

  const togglePlay = async () => {
    const audio = audioRef.current;
    if (!audio) return;

    if (audio.paused) {
      try {
        await audio.play();
        // play 이벤트에서 isPlaying/startRaf 동기화
      } catch {
        setIsPlaying(false);
        stopRaf();
      }
      return;
    }

    audio.pause();
    // pause 이벤트에서 isPlaying/stopRaf 동기화
  };

  const onLoadedMetadata = () => {
    const audio = audioRef.current;
    if (!audio) return;
    setDuration(Number.isFinite(audio.duration) ? audio.duration : 0);
  };

  const onEnded = () => {
    const audio = audioRef.current;
    if (!audio) return;

    stopRaf();
    setIsPlaying(false);

    setCurrentTime(audio.duration || 0);
    setCurrentTime(0);
  };

  const seekByClick = (e: React.MouseEvent<HTMLDivElement>) => {
    const audio = audioRef.current;
    const bar = barRef.current;
    if (!audio || !bar || duration <= 0) return;

    const rect = bar.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const ratio = Math.min(1, Math.max(0, x / rect.width));

    audio.currentTime = ratio * duration;
    setCurrentTime(audio.currentTime);

    if (!audio.paused) startRaf();
  };

  useEffect(() => {
    const audio = audioRef.current;
    if (!audio) return;

    const onPlay = () => {
      setIsPlaying(true);
      startRaf();
    };

    const onPause = () => {
      setIsPlaying(false);
      stopRaf();
      setCurrentTime(audio.currentTime);
    };

    const onSeeking = () => {
      setCurrentTime(audio.currentTime);
    };

    audio.addEventListener('play', onPlay);
    audio.addEventListener('pause', onPause);
    audio.addEventListener('seeking', onSeeking);

    return () => {
      audio.removeEventListener('play', onPlay);
      audio.removeEventListener('pause', onPause);
      audio.removeEventListener('seeking', onSeeking);
      stopRaf();
    };
  }, []);

  useEffect(() => {
    const audio = audioRef.current;
    if (!audio) return;

    stopRaf();
    setIsPlaying(false);
    setDuration(0);
    setCurrentTime(0);
    audio.currentTime = 0;
    audio.pause();
  }, [src]);

  return (
    <div className={cn('flex items-center gap-2', className)}>
      <audio
        ref={audioRef}
        src={src}
        preload='metadata'
        onLoadedMetadata={onLoadedMetadata}
        onEnded={onEnded}
      />

      <button
        type='button'
        onClick={togglePlay}
        aria-label={isPlaying ? 'Pause' : 'Play'}
        className='grid size-8 place-items-center text-gray-200'
      >
        {isPlaying ? <IcPause /> : <IcPlay />}
      </button>

      <div
        ref={barRef}
        onClick={seekByClick}
        role='button'
        aria-label='Seek bar'
        tabIndex={0}
        className='w-28 h-1.25 rounded-20 bg-gray-800 overflow-hidden'
      >
        <div
          className='h-full w-full origin-left bg-gray-300'
          style={{ transform: `scaleX(${progress})` }}
        />
      </div>

      <a
        href={src}
        download
        aria-label='Download'
        className='grid size-8 place-items-center'
      >
        <IcDownload />
      </a>
    </div>
  );
};

export default AudioPlayer;
