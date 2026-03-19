'use client';

import { useState, useEffect, useRef } from 'react';
import { Button } from '@singchronize/ui';
import { BaseModal } from '@/shared/components';
import { getEulReul } from '@/shared/lib/korean';

const DEFAULT_COLOR = '255, 217, 0';

const extractDominantColor = (imgEl: HTMLImageElement): string => {
  const canvas = document.createElement('canvas');
  const ctx = canvas.getContext('2d');
  if (!ctx) return DEFAULT_COLOR;

  canvas.width = 50;
  canvas.height = 50;
  ctx.drawImage(imgEl, 0, 0, 50, 50);

  try {
    const imageData = ctx.getImageData(0, 0, 50, 50);
    const { data } = imageData;
    let r = 0,
      g = 0,
      b = 0,
      count = 0;

    for (let i = 0; i < data.length; i += 4) {
      const r_val = data[i] as number;
      const g_val = data[i + 1] as number;
      const b_val = data[i + 2] as number;

      const brightness = (r_val + g_val + b_val) / 3;
      if (brightness < 20 || brightness > 235) continue;

      r += r_val;
      g += g_val;
      b += b_val;
      count++;
    }

    if (count === 0) return DEFAULT_COLOR;
    return `${Math.round(r / count)}, ${Math.round(g / count)}, ${Math.round(b / count)}`;
  } catch {
    return DEFAULT_COLOR;
  }
};

interface ListenSongModalProps {
  artistName: string;
  songTitle: string;
  thumbnail: string;
  onClose: () => void;
}

const ListenSongModal = ({
  artistName,
  songTitle,
  thumbnail,
  onClose,
}: ListenSongModalProps) => {
  const imgRef = useRef<HTMLImageElement>(null);
  const [dominantColor, setDominantColor] = useState<string>(DEFAULT_COLOR);

  useEffect(() => {
    const img = imgRef.current;
    if (!img) return;

    const handleLoad = () => setDominantColor(extractDominantColor(img));

    if (img.complete) handleLoad();
    else {
      img.addEventListener('load', handleLoad);
      return () => img.removeEventListener('load', handleLoad);
    }
  }, [thumbnail]);

  const handleListen = () => {
    const query = encodeURIComponent(`${artistName} ${songTitle}`);
    window.open(`https://www.youtube.com/results?search_query=${query}`, '_blank');
    onClose();
  };

  return (
    <BaseModal
      onClose={onClose}
      className='relative flex flex-col justify-center items-center gap-23.5 w-full max-w-199 max-h-159 h-[70vh] bg-bg rounded-20'
    >
      {/* 그라데이션 배경 */}
      <div
        className='absolute inset-0 z-0'
        style={{
          background: `radial-gradient(ellipse at bottom, rgba(${dominantColor}, 0.17) 0%, rgba(22, 22, 22, 0.17) 70%)`,
        }}
      />

      <div className='flex flex-col items-center gap-11 z-10'>
        <div className='aspect-square size-38.5 overflow-hidden rounded-10 bg-gray-800'>
          {thumbnail ? (
            <img
              ref={imgRef}
              src={thumbnail}
              alt={songTitle}
              className='size-full object-cover'
            />
          ) : (
            <div className='size-full bg-white-10' />
          )}
        </div>

        <div className='flex flex-col items-center gap-2 text-center'>
          <h2 className='typo-32b text-white'>
            {artistName}의 {songTitle}
            {getEulReul(songTitle)} 들어볼까요?
          </h2>
          <p className='typo-16r text-gray-200'>
            노래 듣기 버튼을 누르면 YouTube로 이동합니다
          </p>
        </div>
      </div>

      <div className='flex gap-3 z-10'>
        <Button variant='outline' onClick={onClose}>
          뒤로가기
        </Button>
        <Button onClick={handleListen}>노래 듣기</Button>
      </div>
    </BaseModal>
  );
};

export default ListenSongModal;
