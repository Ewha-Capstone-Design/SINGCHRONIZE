'use client';

import { useMemo, useState } from 'react';
import { BaseModal } from '@/shared/components';
import { InputField, Button } from '@singchronize/ui';
import { ArtistCard } from '@/entities/artist/ui';
import type { ArtistUiType } from '@/entities/artist/model/types';

import { MOCK_ALL_ARTISTS } from '@/entities/artist/model/mock';

type EditFavoriteArtistsModalProps = {
  initialSelectedIds?: number[];
  onClose: () => void;
  onConfirm: (selectedArtists: ArtistUiType[]) => void;
};

const EditFavoriteArtistsModal = ({
  initialSelectedIds = [],
  onClose,
  onConfirm,
}: EditFavoriteArtistsModalProps) => {
  const [query, setQuery] = useState('');
  const [selectedIds, setSelectedIds] = useState<Set<number>>(
    () => new Set(initialSelectedIds)
  );

  const filteredArtists = useMemo(() => {
    const q = query.trim();
    if (!q) return MOCK_ALL_ARTISTS;
    return MOCK_ALL_ARTISTS.filter((artist) => artist.name.includes(q));
  }, [query]);

  const toggleArtist = (artistId: number) => {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(artistId)) next.delete(artistId);
      else next.add(artistId);
      return next;
    });
  };

  const handleConfirm = () => {
    const selected = MOCK_ALL_ARTISTS.filter((a) => selectedIds.has(a.id));
    onConfirm(selected);
    onClose();
  };

  return (
    <BaseModal
      onClose={onClose}
      className='relative px-10 flex flex-col w-full max-w-226 max-h-178 h-[70vh] bg-bg rounded-20'
    >
      <div className='pt-14.5 flex flex-col gap-9 h-full'>
        <h2 className='typo-28b text-white'>선호하는 가수 수정하기</h2>

        <div className='mx-auto flex flex-1 flex-col gap-6 min-w-120.5 w-fit overflow-y-hidden'>
          <InputField
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder='가수 이름을 입력해주세요'
          />

          <div className='grid grid-cols-3 gap-4 overflow-y-auto scrollbar-hide'>
            {filteredArtists.map((artist) => (
              <ArtistCard
                key={artist.id}
                artist={artist}
                isSelected={selectedIds.has(artist.id)}
                onToggle={toggleArtist}
              />
            ))}
          </div>
        </div>

        <div className='py-7 mx-auto'>
          <Button onClick={handleConfirm}>선택 완료하기</Button>
        </div>
      </div>
    </BaseModal>
  );
};

export default EditFavoriteArtistsModal;
