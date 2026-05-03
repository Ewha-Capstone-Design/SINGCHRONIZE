'use client';

import { useState, useEffect } from 'react';
import NextImage from 'next/image';
import { cn } from '@/shared/lib/cn';

type AppImageProps = {
  src?: string | null;
  alt: string;
  fill?: boolean;
  width?: number;
  height?: number;
  className?: string;
};

const AppImage = ({ src, alt, fill, width, height, className }: AppImageProps) => {
  const [error, setError] = useState(false);

  useEffect(() => {
    setError(false);
  }, [src]);

  const validSrc = src && /^(https?:\/\/|\/|blob:|data:)/.test(src) ? src : null;

  if (!validSrc || error) {
    return <div className={cn('bg-gray-700', className)} />;
  }

  const isLocal = validSrc.startsWith('blob:') || validSrc.startsWith('data:');

  return (
    <NextImage
      src={validSrc}
      alt={alt}
      fill={fill}
      width={!fill ? width : undefined}
      height={!fill ? height : undefined}
      unoptimized={isLocal}
      className={className}
      onError={() => setError(true)}
    />
  );
};

export default AppImage;
