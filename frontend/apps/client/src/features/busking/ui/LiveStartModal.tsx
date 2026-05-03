'use client';

import { useState } from 'react';
import { cn } from '@/shared/lib/cn';
import { BaseModal } from '@/shared/components';
import { useNavigate } from '@/shared/lib/navigation';
import { useThumbnail } from '@/shared/hooks';
import { LiveStartStep1 } from './LiveStartStep1';
import { LiveStartStep2 } from './LiveStartStep2';

import { getApiErrorMessage } from '@/shared/api/apiError';
import type { SongUiType } from '@/entities/song/model/types';
import {
  useCreateBuskingRoom,
  useGetThumbnailPresignedUrl,
  useStartBuskingRoom,
} from '@/entities/busking';

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
  const [isSubmitting, setIsSubmitting] = useState(false);

  const { preview, thumbnail, handleThumbnailChange, clearThumbnail } = useThumbnail();
  const { mutateAsync: getPresignedUrl } = useGetThumbnailPresignedUrl();
  const { mutateAsync: createRoom } = useCreateBuskingRoom();
  const { mutateAsync: startRoom } = useStartBuskingRoom();

  const handleToggleSong = (song: SongUiType) => {
    const isSelected = selectedSongs.some((s) => s.id === song.id);
    if (isSelected) {
      setSelectedSongs((prev) => prev.filter((s) => s.id !== song.id));
    } else if (selectedSongs.length < MAX_SETLIST) {
      setSelectedSongs((prev) => [...prev, song]);
    }
  };

  const handleStart = async () => {
    if (isSubmitting) return;
    setIsSubmitting(true);

    try {
      let thumbnailUrl: string | null = null;

      // 썸네일이 있으면 presigned URL로 S3 업로드
      if (thumbnail?.file) {
        const { upload_url, s3_url } = await getPresignedUrl();
        await fetch(upload_url, { method: 'PUT', body: thumbnail.file });
        thumbnailUrl = s3_url;
      }

      const room = await createRoom({
        title: title.trim(),
        thumbnail_url: thumbnailUrl,
        setlist: selectedSongs.map((song, index) => ({
          song_id: String(song.id),
          title: song.title,
          artist: song.artist,
          album_art_url: song.thumbnail ?? null,
          order_index: index,
        })),
      });

      await startRoom(room.id);

      sessionStorage.setItem(
        `livekit_host_${room.id}`,
        JSON.stringify({ token: room.livekit_token, url: room.livekit_url }),
      );

      go(dynamic.liveRoom(room.id, 'live'));
    } catch (err) {
      alert(getApiErrorMessage(err, '버스킹 시작에 실패했습니다.'));
    } finally {
      setIsSubmitting(false);
    }
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
          : 'px-17 py-12 pb-0 max-w-310 max-h-198 h-[80vh]',
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
          isSubmitting={isSubmitting}
        />
      )}
    </BaseModal>
  );
};

export default LiveStartModal;
