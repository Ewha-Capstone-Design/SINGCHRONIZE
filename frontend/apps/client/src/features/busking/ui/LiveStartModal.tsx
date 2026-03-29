'use client';

import { useEffect, useState } from 'react';
import { cn } from '@/shared/lib/cn';
import { BaseModal } from '@/shared/components';
import { useNavigate } from '@/shared/lib/navigation';
import { useThumbnail } from '@/shared/hooks';
import { LiveStartStep1 } from './LiveStartStep1';
import { LiveStartStep2 } from './LiveStartStep2';
import type { SongUiType } from '@/entities/song/model/types';

type LiveStartModalProps = {
  open: boolean;
  onClose: () => void;
};

type Step = 1 | 2;

const MAX_SETLIST = 5;

const LiveStartModal = ({ open, onClose }: LiveStartModalProps) => {
  const { go, dynamic } = useNavigate();

  const [step, setStep] = useState<Step>(1);
  const [title, setTitle] = useState('');
  const [keyword, setKeyword] = useState('');
  const [selectedSongs, setSelectedSongs] = useState<SongUiType[]>([]);

  const { preview, thumbnail, handleThumbnailChange, clearThumbnail } = useThumbnail();

  const handleToggleSong = (song: SongUiType) => {
    const isSelected = selectedSongs.some((s) => s.id === song.id);
    if (isSelected) {
      setSelectedSongs((prev) => prev.filter((s) => s.id !== song.id));
    } else if (selectedSongs.length < MAX_SETLIST) {
      setSelectedSongs((prev) => [...prev, song]);
    }
  };

  const handleStart = () => {
    console.log({
      title: title.trim(),
      thumbnail: thumbnail?.file ?? null,
      setlist: selectedSongs,
    });
    // TODO: API 연결 후 roomId 받아서 dynamic.liveRoom(roomId)로 교체
    go(dynamic.liveRoom('1', 'live'));
  };

  const handleClose = () => {
    setStep(1);
    setTitle('');
    clearThumbnail();
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
          ? 'px-25 pt-14.5 pb-12.5 max-w-198 max-h-178 h-[70vh]'
          : 'px-17 py-12 pb-0 max-w-310 max-h-198 h-[80vh]'
      )}
    >
      {step === 1 ? (
        <LiveStartStep1
          title={title}
          preview={preview}
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
