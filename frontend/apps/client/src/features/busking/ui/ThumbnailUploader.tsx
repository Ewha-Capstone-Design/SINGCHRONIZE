'use client';

import { IcPlus } from '@/shared/assets/icons';

type ThumbnailUploaderProps = {
  preview: string | null;
  onChange: (file: File, preview: string) => void;
};

export const ThumbnailUploader = ({ preview, onChange }: ThumbnailUploaderProps) => {
  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const url = URL.createObjectURL(file);
    onChange(file, url);
  };

  return (
    <label className='relative flex items-center justify-center w-103 aspect-video cursor-pointer overflow-hidden rounded-10 bg-gray-800 text-gray-300'>
      {preview ? (
        <img src={preview} alt='라이브 버스킹 썸네일' className='h-full object-cover' />
      ) : (
        <IcPlus />
      )}
      <input type='file' accept='image/*' className='hidden' onChange={handleChange} />
    </label>
  );
};
