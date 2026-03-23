'use client';

import { useEffect, useState } from 'react';
import { cn } from '@/shared/lib/cn';
import { BaseModal } from '@/shared/components';
import { useNavigate } from '@/shared/lib/navigation';
import { LiveStartStep1 } from './LiveStartStep1';
import { LiveStartStep2 } from './LiveStartStep2';
import type { SongUiType } from '@/entities/song/model/types';

type LiveStartModalProps = {
  open: boolean;
  onClose: () => void;
  onSubmit?: (payload: {
    title: string;
    thumbnail: File | null;
    setlist: SongUiType[];
  }) => void;
};

type Step = 1 | 2;

const MAX_SETLIST = 5;

const LiveStartModal = ({ open, onClose, onSubmit }: LiveStartModalProps) => {
  const { go, ROUTES, dynamic } = useNavigate();

  const [step, setStep] = useState<Step>(1);
  const [title, setTitle] = useState('');
  const [thumbnailFile, setThumbnailFile] = useState<File | null>(null);
  const [thumbnailPreview, setThumbnailPreview] = useState<string | null>(null);
  const [keyword, setKeyword] = useState('');
  const [selectedSongs, setSelectedSongs] = useState<SongUiType[]>([]);

  useEffect(() => {
    if (!open) return;
    const prev = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    return () => {
      document.body.style.overflow = prev;
    };
  }, [open]);

  useEffect(() => {
    return () => {
      if (thumbnailPreview) URL.revokeObjectURL(thumbnailPreview);
    };
  }, [thumbnailPreview]);

  const handleThumbnailChange = (file: File, preview: string) => {
    if (thumbnailPreview) URL.revokeObjectURL(thumbnailPreview);
    setThumbnailFile(file);
    setThumbnailPreview(preview);
  };

  const handleToggleSong = (song: SongUiType) => {
    const isSelected = selectedSongs.some((s) => s.id === song.id);
    if (isSelected) {
      setSelectedSongs((prev) => prev.filter((s) => s.id !== song.id));
    } else if (selectedSongs.length < MAX_SETLIST) {
      setSelectedSongs((prev) => [...prev, song]);
    }
  };

  const handleStart = () => {
    onSubmit?.({ title: title.trim(), thumbnail: thumbnailFile, setlist: selectedSongs });
    // TODO: API 연결 후 roomId 받아서 dynamic.liveRoom(roomId) 로 교체
    go(dynamic.liveRoom('1'));
  };

  const handleClose = () => {
    setStep(1);
    setTitle('');
    setThumbnailFile(null);
    if (thumbnailPreview) URL.revokeObjectURL(thumbnailPreview);
    setThumbnailPreview(null);
    setKeyword('');
    setSelectedSongs([]);
    onClose();
  };

  if (!open) return null;

  return (
    <BaseModal
      onClose={handleClose}
      className={cn(
        'relative flex flex-col w-full bg-bg rounded-20',
        'overflow-y-auto scrollbar-hide',
        step === 1
          ? 'px-25 py-12 max-w-198 max-h-178 h-[70vh]'
          : 'px-17 py-12 pb-0 max-w-310 max-h-198 h-[80vh]'
      )}
    >
      {step === 1 ? (
        <LiveStartStep1
          title={title}
          thumbnailPreview={thumbnailPreview}
          onTitleChange={setTitle}
          onThumbnailChange={handleThumbnailChange}
          onNext={() => setStep(2)}
        />
      ) : (
        <LiveStartStep2
          keyword={keyword}
          selectedSongs={selectedSongs}
          onKeywordChange={setKeyword}
          onToggleSong={handleToggleSong}
          onSetlistChange={setSelectedSongs}
          onStart={handleStart}
        />
      )}
    </BaseModal>
  );
};

export default LiveStartModal;
