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
import { BuskingSection } from '@/widgets/busking-list/ui';
import { ListenSongModal } from '@/features/listen-song';
import { SongUiType } from '@/entities/song/model/types';

import { useMe } from '@/entities/user';
import { useHomeFeeds } from '@/entities/home';
import { useVocalProfile } from '@/entities/analysis';

const HomePage = () => {
  const [selectedSong, setSelectedSong] = useState<SongUiType | null>(null);
  const { open, openModal, closeModal } = useModal();

  const { data: me } = useMe();
  const { data: homeFeeds } = useHomeFeeds();
  const { data: vocalProfile } = useVocalProfile();

  const handleSongClick = useCallback(
    (song: SongUiType) => {
      setSelectedSong(song);
      openModal();
    },
    [openModal],
  );

  const handleClose = useCallback(() => {
    closeModal();
    setSelectedSong(null);
  }, [closeModal]);

  return (
    <main>
      <HomeHeader username={me?.nickname} profileImageUrl={me?.profileImage} />
      <VocalAnalysisBanner size='home' />
      <div
        className={cn(
          'mt-8 px-9 pb-9 grid gap-9',
          'grid-cols-1',
          'lg:grid-cols-[minmax(0,1fr)_340px]',
          'xl:grid-cols-[minmax(0,1fr)_400px]',
        )}
      >
        <div className='flex flex-col min-w-0'>
          {!!vocalProfile?.updated_at && <SimilarVocalSection onSongClick={handleSongClick} />}
          <div className='flex flex-col gap-6'>
            <BuskingSection
              title='지금 인기 있는 버스킹'
              cardVariant='sm'
              px={0}
              items={homeFeeds?.liveTicker ?? []}
            />
            <BuskingSection
              title='NOW ON AIR! 최근 업로드된 버스킹'
              cardVariant='sm'
              px={0}
              items={homeFeeds?.liveTicker ?? []}
            />
          </div>
        </div>

        <div className='flex flex-col gap-12'>
          <WeeklyChart items={homeFeeds?.weekly ?? []} onSongClick={handleSongClick} />
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
