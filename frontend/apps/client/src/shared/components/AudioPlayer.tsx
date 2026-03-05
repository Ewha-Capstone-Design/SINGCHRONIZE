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

  const [isPlaying, setIsPlaying] = useState(false);
  const [duration, setDuration] = useState(0);
  const [currentTime, setCurrentTime] = useState(0);

  const progressPercent = useMemo(() => {
    if (duration <= 0) return 0;
    const v = (currentTime / duration) * 100;
    return Math.min(100, Math.max(0, v));
  }, [currentTime, duration]);

  const togglePlay = async () => {
    const audio = audioRef.current;
    if (!audio) return;

    if (audio.paused) {
      try {
        await audio.play();
        setIsPlaying(true);
      } catch {
        setIsPlaying(false);
      }
      return;
    }

    audio.pause();
    setIsPlaying(false);
  };

  const onLoadedMetadata = () => {
    const audio = audioRef.current;
    if (!audio) return;
    setDuration(Number.isFinite(audio.duration) ? audio.duration : 0);
  };

  const onTimeUpdate = () => {
    const audio = audioRef.current;
    if (!audio) return;
    setCurrentTime(audio.currentTime);
  };

  const onEnded = () => {
    setIsPlaying(false);
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
  };

  useEffect(() => {
    const audio = audioRef.current;
    if (!audio) return;

    const syncPlayState = () => setIsPlaying(!audio.paused);

    audio.addEventListener('play', syncPlayState);
    audio.addEventListener('pause', syncPlayState);

    return () => {
      audio.removeEventListener('play', syncPlayState);
      audio.removeEventListener('pause', syncPlayState);
    };
  }, []);

  return (
    <div className={cn('flex items-center gap-2', className)}>
      <audio
        ref={audioRef}
        src={src}
        preload='metadata'
        onLoadedMetadata={onLoadedMetadata}
        onTimeUpdate={onTimeUpdate}
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
          className='h-full bg-gray-300 transition-[width] duration-150 ease-linear'
          style={{ width: `${progressPercent}%` }}
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
