import { useCallback, useEffect, useState } from 'react';

type Thumbnail = {
  file: File;
  preview: string;
};

const useThumbnail = () => {
  const [thumbnail, setThumbnail] = useState<Thumbnail | null>(null);

  const handleThumbnailChange = useCallback((file: File, preview: string) => {
    setThumbnail((prev) => {
      if (prev?.preview) URL.revokeObjectURL(prev.preview);
      return { file, preview };
    });
  }, []);

  const clearThumbnail = useCallback(() => {
    setThumbnail((prev) => {
      if (prev?.preview) URL.revokeObjectURL(prev.preview);
      return null;
    });
  }, []);

  useEffect(() => {
    return () => {
      if (thumbnail?.preview) {
        URL.revokeObjectURL(thumbnail.preview);
      }
    };
  }, [thumbnail]);

  return {
    thumbnail,
    preview: thumbnail?.preview ?? null,
    handleThumbnailChange,
    clearThumbnail,
  };
};

export default useThumbnail;
