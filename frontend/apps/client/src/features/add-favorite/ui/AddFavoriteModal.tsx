'use client';

import { useState } from 'react';
import { InputField } from '@singchronize/ui';
import { BaseModal } from '@/shared/components';
import { LikeIconButton, SongListItem } from '@/entities/song/ui';
import type { SongUiType } from '@/entities/song/model/types';

import { useSearchMusic } from '@/entities/song';
import { useAddWishlistItem, useDeleteWishlistItem, useWishlist } from '@/entities/library';

type AddFavoriteModalProps = {
  folderId?: string;
  onClose: () => void;
};

const AddFavoriteModal = ({ folderId, onClose }: AddFavoriteModalProps) => {
  const [query, setQuery] = useState('');
  const [addingIds, setAddingIds] = useState<Set<string>>(() => new Set());

  const { mutate: addWishlistItem } = useAddWishlistItem();
  const { mutate: deleteWishlistItem } = useDeleteWishlistItem();
  const { data: searchedItems = [] } = useSearchMusic(query);
  const { data: wishlistItems = [] } = useWishlist(folderId);

  const toggleLike = (song: SongUiType) => {
    const id = String(song.id);
    if (addingIds.has(id)) return;

    const existing = wishlistItems.find((item) => item.songId === id);
    if (existing) {
      deleteWishlistItem(existing.itemId);
      return;
    }

    setAddingIds((prev) => new Set(prev).add(id));

    addWishlistItem(
      {
        song_data: {
          name: song.title,
          artist: song.artist,
          album_image: song.thumbnail ?? null,
          uri: id,
        } as unknown as Record<string, never>,
        folder_id: folderId,
      },
      {
        onSettled: () => {
          setAddingIds((prev) => { const next = new Set(prev); next.delete(id); return next; });
        },
      },
    );
  };

  return (
    <BaseModal
      onClose={onClose}
      className='relative px-25 flex flex-col w-full max-w-226 max-h-178 h-[70vh] bg-bg rounded-20'
    >
      <div className='pt-14.5 flex flex-col gap-7 h-full'>
        <div className='flex flex-col gap-7'>
          <h2 className='typo-28b text-white'>찜 추가하기</h2>
          <InputField
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder='노래 제목이나 가수를 입력해주세요'
          />
        </div>

        {searchedItems.length === 0 ? (
          <div className='flex flex-1 flex-col items-center justify-center'>
            <p className='typo-20r text-gray-500'>검색 결과가 없어요</p>
            <p className='typo-20r text-gray-500'>다른 키워드로 다시 검색해 보세요!</p>
          </div>
        ) : (
          <div className='pb-7 flex flex-col gap-4 overflow-y-auto min-h-0 scrollbar-hide'>
            {searchedItems.map((song) => (
              <SongListItem
                key={song.id}
                variant='list3'
                title={song.title}
                artist={song.artist}
                thumbnail={song.thumbnail ?? ''}
                rightSlot={
                  <LikeIconButton
                    isLiked={wishlistItems.some((item) => item.songId === String(song.id))}
                    onClick={() => toggleLike(song)}
                    disabled={addingIds.has(String(song.id))}
                  />
                }
              />
            ))}
          </div>
        )}
      </div>
    </BaseModal>
  );
};

export default AddFavoriteModal;
