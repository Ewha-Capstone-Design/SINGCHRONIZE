'use client';

import { useCallback, useState } from 'react';
import { useModal } from '@/shared/hooks';
import { cn } from '@/shared/lib/cn';
import {
  ArchivePreview,
  HomeHeader,
  WeeklyChart,
  SimilarVocalSection,
} from '@/widgets/home/ui';
import { VocalAnalysisBanner } from '@/widgets/vocal-analyze/ui';
import { SongUiType } from '@/entities/song/model/types';
import { ListenSongModal } from '@/features/listen-song';

const HomePage = () => {
  const [selectedSong, setSelectedSong] = useState<SongUiType | null>(null);
  const { open, openModal, closeModal } = useModal();

  const handleSongClick = useCallback(
    (song: SongUiType) => {
      setSelectedSong(song);
      openModal();
    },
    [openModal]
  );

  const handleClose = useCallback(() => {
    closeModal();
    setSelectedSong(null);
  }, [closeModal]);

  return (
    <main>
      <HomeHeader />

      <div
        className={cn(
          'px-9 pb-9 grid gap-9',
          'grid-cols-1',
          'lg:grid-cols-[minmax(0,1fr)_340px]',
          'xl:grid-cols-[minmax(0,1fr)_400px]'
        )}
      >
        <div className='flex flex-col gap-8 min-w-0'>
          <VocalAnalysisBanner size='compact' />
          <SimilarVocalSection onSongClick={handleSongClick} />
          {/* TODO: 라이브 기능 디자인 위치 */}
        </div>

        <div className='flex flex-col gap-12'>
          <WeeklyChart onSongClick={handleSongClick} />
          <ArchivePreview />
        </div>
      </div>

      {open && selectedSong && (
        <ListenSongModal
          artistName={selectedSong.artist}
          songTitle={selectedSong.title}
          thumbnail={selectedSong.thumbnail ?? ''}
          onClose={handleClose}
        />
      )}
    </main>
  );
};

export default HomePage;
