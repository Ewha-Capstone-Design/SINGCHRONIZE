'use client';

import { useState } from 'react';
import { cn } from '@/shared/lib/cn';
import { useThumbnail } from '@/shared/hooks';
import { BaseModal } from '@/shared/components';
import { RecordUploadStep1 } from './RecordUploadStep1';
import { RecordUploadStep2 } from './RecordUploadStep2';
import type { SongUiType } from '@/entities/song/model/types';

type RecordUploadModalProps = {
  open: boolean;
  onClose: () => void;
};

type Step = 1 | 2;

const RecordUploadModal = ({ open, onClose }: RecordUploadModalProps) => {
  const [step, setStep] = useState<Step>(1);
  const [title, setTitle] = useState('');
  const [recordFile, setRecordFile] = useState<File | null>(null);
  const [keyword, setKeyword] = useState('');
  const [selectedSongs, setSelectedSongs] = useState<SongUiType[]>([]);
  const [endDate, setEndDate] = useState<Date | undefined>();

  const { preview, thumbnail, handleThumbnailChange, clearThumbnail } = useThumbnail();

  const handleToggleSong = (song: SongUiType) => {
    const isSelected = selectedSongs.some((s) => s.id === song.id);
    setSelectedSongs((prev) =>
      isSelected ? prev.filter((s) => s.id !== song.id) : [...prev, song]
    );
  };

  const handleSubmit = () => {
    console.log({
      title: title.trim(),
      file: recordFile,
      thumbnail: thumbnail?.file ?? null,
      setlist: selectedSongs,
      endDate,
    });

    handleClose();
  };

  const handleClose = () => {
    setStep(1);
    setTitle('');
    setRecordFile(null);
    setKeyword('');
    setSelectedSongs([]);
    setEndDate(undefined);
    clearThumbnail();
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
        <RecordUploadStep1
          title={title}
          onTitleChange={setTitle}
          preview={preview}
          onThumbnailChange={handleThumbnailChange}
          onNext={() => setStep(2)}
        />
      ) : (
        <RecordUploadStep2
          keyword={keyword}
          selectedSongs={selectedSongs}
          endDate={endDate}
          onKeywordChange={setKeyword}
          onToggleSong={handleToggleSong}
          onSetlistChange={setSelectedSongs}
          onEndDateChange={setEndDate}
          onSubmit={handleSubmit}
        />
      )}
    </BaseModal>
  );
};

export default RecordUploadModal;
