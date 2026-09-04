'use client';

import { useState } from 'react';
import { cn } from '@/shared/lib/cn';
import { useThumbnail } from '@/shared/hooks';
import { BaseModal } from '@/shared/components';
import { RecordUploadStep1 } from './RecordUploadStep1';
import { RecordUploadStep2 } from './RecordUploadStep2';
import { RecordUploadComplete } from './RecordUploadComplete';
import type { SongUiType } from '@/entities/song/model/types';

import { recordedBuskingApi, uploadFileToS3 } from '@/entities/busking';

type RecordUploadModalProps = {
  open: boolean;
  onClose: () => void;
};

type Step = 1 | 2 | 3;

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
    setSelectedSongs(isSelected ? [] : [song]);
  };

  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async () => {
    if (isSubmitting || !recordFile || selectedSongs.length === 0 || !endDate) return;
    setIsSubmitting(true);

    try {
      // 1. 녹음 파일 presigned URL 발급 → S3 업로드
      const { upload_url: recordUploadUrl, s3_key } =
        await recordedBuskingApi.getRecordingUploadUrl();
      await uploadFileToS3(recordUploadUrl, recordFile, 'audio/m4a');

      // 2. 썸네일 S3 업로드 (선택)
      let thumbnailUrl: string | null = null;
      if (thumbnail?.file) {
        const { upload_url: thumbUploadUrl, s3_url } =
          await recordedBuskingApi.getThumbnailPresignedUrl();
        await uploadFileToS3(
          thumbUploadUrl,
          thumbnail.file,
          thumbnail.file.type || 'image/jpeg',
        );
        thumbnailUrl = s3_url;
      }

      // 3. 녹음 버스킹 생성
      const song = selectedSongs[0]!;
      await recordedBuskingApi.createRecordedBusking({
        title: title.trim(),
        thumbnail_url: thumbnailUrl,
        s3_key,
        song_data: {
          name: song.title,
          artist: song.artist,
          album_image: song.thumbnail ?? null,
          uri: String(song.id),
        },
        vote_ends_at: endDate.toISOString(),
      });

      setStep(3);
    } catch {
      alert('업로드에 실패했습니다. 다시 시도해주세요.');
    } finally {
      setIsSubmitting(false);
    }
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
        step === 1
          ? 'px-25 pt-14.5 pb-12.5 max-w-198 max-h-178 h-[70vh] overflow-y-auto scrollbar-hide'
          : step === 2
            ? 'px-17 py-12 pb-0 max-w-310 max-h-198 h-[80vh]'
            : 'px-25 py-16 max-w-198 max-h-178 h-[70vh] overflow-y-auto scrollbar-hide',
      )}
    >
      {step === 1 && (
        <RecordUploadStep1
          title={title}
          onTitleChange={setTitle}
          preview={preview}
          onThumbnailChange={handleThumbnailChange}
          onNext={() => setStep(2)}
        />
      )}
      {step === 2 && (
        <RecordUploadStep2
          keyword={keyword}
          selectedSongs={selectedSongs}
          endDate={endDate}
          recordFile={recordFile}
          onKeywordChange={setKeyword}
          onToggleSong={handleToggleSong}
          onSetlistChange={setSelectedSongs}
          onEndDateChange={setEndDate}
          onRecordFileChange={setRecordFile}
          onSubmit={handleSubmit}
          isSubmitting={isSubmitting}
        />
      )}
      {step === 3 && (
        <RecordUploadComplete thumbnailPreview={preview} onClose={handleClose} />
      )}
    </BaseModal>
  );
};

export default RecordUploadModal;
