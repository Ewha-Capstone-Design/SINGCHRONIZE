'use client';

import { cn } from '@/shared/lib/cn';
import { SongListItem } from '@/entities/song/ui';
import { IcDownload } from '@/shared/assets/icons';
import { SongBlockMenu } from '@/features/block';
import { SongLikeButton } from '@/features/like';
import { ArchiveSectionUiType } from '../model/types';

type ArchiveSectionProps = {
  group: ArchiveSectionUiType;
};

const ArchiveSection = ({ group }: ArchiveSectionProps) => {
  const handleDownload = () => {
    if (group.recordingUrl) {
      window.open(group.recordingUrl, '_blank', 'noopener,noreferrer');
    }
  };

  return (
    <section
      className={cn(
        'px-10 py-7 flex flex-col gap-4 bg-gray-900 border-2 border-gray-800 rounded-10',
      )}
    >
      <div className='flex items-center justify-between gap-4'>
        <h3 className='typo-24b text-white'>{group.title}</h3>

        <button
          type='button'
          onClick={handleDownload}
          disabled={!group.recordingUrl}
          className={cn(
            'inline-flex items-center gap-1 text-gray-200',
            'disabled:cursor-default',
          )}
        >
          <IcDownload />
          <span className='typo-16r'>녹음 다운로드</span>
        </button>
      </div>

      <div className='grid grid-cols-2 gap-4'>
        {group.songs.map((song) => (
          <SongListItem
            key={song.id}
            variant='list3'
            thumbnail={song.thumbnail}
            title={song.title}
            artist={song.artist}
            rightSlot={
              <div className='flex items-center gap-4'>
                <SongLikeButton
                  songId={String(song.id)}
                  isLiked={song.isLiked ?? false}
                  song={song}
                />
                <SongBlockMenu songId={String(song.id)} />
              </div>
            }
          />
        ))}
      </div>
    </section>
  );
};

export default ArchiveSection;
