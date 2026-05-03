'use client';

import { IcPlus } from '@/shared/assets/icons';
import { AppImage } from '@/shared/components';

type ThumbnailUploaderProps = {
  preview: string | null;
  onChange: (file: File, preview: string) => void;
};

const ThumbnailUploader = ({ preview, onChange }: ThumbnailUploaderProps) => {
  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const url = URL.createObjectURL(file);
    onChange(file, url);
  };

  return (
    <label className='relative flex items-center justify-center w-103 aspect-video cursor-pointer overflow-hidden rounded-10 bg-gray-800 text-gray-300'>
      {preview ? (
        <AppImage src={preview} alt='thumbnail' fill className='object-cover' />
      ) : (
        <IcPlus />
      )}
      <input type='file' accept='image/*' className='hidden' onChange={handleChange} />
    </label>
  );
};

export default ThumbnailUploader;
