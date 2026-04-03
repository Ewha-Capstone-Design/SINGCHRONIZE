'use client';

import { Button } from '@singchronize/ui';
import { cn } from '@/shared/lib/cn';
import { useModal } from '@/shared/hooks';
import { BackButton } from '@/shared/components';
import { AddFavoriteModal } from '@/features/add-favorite';
import { SongBlockMenu } from '@/features/block';
import { SongLikeButton } from '@/features/like';
import { SongListItem } from '@/entities/song/ui';
import type { FavoriteFolderUiType } from '@/entities/library/model/types';

import { useWishlist } from '@/entities/library';

interface FavoriteFolderDetailProps {
  folder: FavoriteFolderUiType;
  onBack: () => void;
}

const FavoriteFolderDetail = ({ folder, onBack }: FavoriteFolderDetailProps) => {
  const { open: isAddModalOpen, openModal, closeModal } = useModal(false);

  const { data: songs = [] } = useWishlist(folder.id);

  return (
    <section className='flex flex-col'>
      <Button variant='normal' className='my-6 w-fit' onClick={openModal}>
        찜 추가하기
      </Button>

      <div className='flex gap-3'>
        <BackButton onClick={onBack} />
        <h2 className='typo-24b text-gray-100'>{folder.name}</h2>
      </div>

      {songs.length > 0 && (
        <ul
          className={cn(
            'mt-2 px-10 py-7 flex flex-col gap-4',
            'rounded-10 border-2 border-gray-800 bg-gray-900',
          )}
        >
          {songs.map((song) => (
            <li key={song.itemId}>
              <SongListItem
                variant='list3'
                thumbnail={song.thumbnail}
                title={song.title}
                artist={song.artist}
                rightSlot={
                  <div className='flex items-center gap-4'>
                    <SongLikeButton
                      isLiked={song.isLiked}
                      songId={song.songId}
                      folderId={folder.id}
                    />
                    <SongBlockMenu songId={song.songId} />
                  </div>
                }
              />
            </li>
          ))}
        </ul>
      )}

      {isAddModalOpen && <AddFavoriteModal folderId={folder.id} onClose={closeModal} />}
    </section>
  );
};

export default FavoriteFolderDetail;
