import { useState } from 'react';

type Thumbnail = {
  file: File;
  preview: string;
};

const useThumbnail = () => {
  const [thumbnail, setThumbnail] = useState<Thumbnail | null>(null);

  const handleThumbnailChange = (file: File, preview: string) => {
    setThumbnail((prev) => {
      if (prev?.preview) URL.revokeObjectURL(prev.preview);
      return { file, preview };
    });
  };

  const clearThumbnail = () => {
    setThumbnail((prev) => {
      if (prev?.preview) URL.revokeObjectURL(prev.preview);
      return null;
    });
  };

  return {
    thumbnail,
    preview: thumbnail?.preview ?? null,
    handleThumbnailChange,
    clearThumbnail,
  };
};

export default useThumbnail;
