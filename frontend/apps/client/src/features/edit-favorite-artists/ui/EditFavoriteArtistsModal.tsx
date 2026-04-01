'use client';

import { useState } from 'react';
import { BaseModal } from '@/shared/components';
import { InputField, Button } from '@singchronize/ui';
import { ArtistCard } from '@/entities/artist/ui';
import type { ArtistUiType } from '@/entities/artist/model/types';

import { useSearchSingers } from '@/entities/artist';

type EditFavoriteArtistsModalProps = {
  initialSelectedArtists?: ArtistUiType[];
  onClose: () => void;
  onConfirm: (selectedArtists: ArtistUiType[]) => void;
};

const EditFavoriteArtistsModal = ({
  initialSelectedArtists = [],
  onClose,
  onConfirm,
}: EditFavoriteArtistsModalProps) => {
  const [query, setQuery] = useState('');
  const [selectedArtists, setSelectedArtists] = useState<Map<number, ArtistUiType>>(
    () => new Map(initialSelectedArtists.map((a) => [a.id, a])),
  );

  const { data: searchResults = [] } = useSearchSingers(query.trim());

  const isSearching = query.trim().length > 0;
  const displayedArtists = isSearching
    ? searchResults
    : Array.from(selectedArtists.values());

  const toggleArtist = (artistId: number) => {
    setSelectedArtists((prev) => {
      const next = new Map(prev);
      if (next.has(artistId)) {
        next.delete(artistId);
      } else {
        const artist = searchResults.find((a) => a.id === artistId);
        if (artist) next.set(artistId, artist);
      }
      return next;
    });
  };

  const handleConfirm = () => {
    onConfirm(Array.from(selectedArtists.values()));
    onClose();
  };

  return (
    <BaseModal
      onClose={onClose}
      className='relative px-25 flex flex-col w-full max-w-226 max-h-178 h-[70vh] bg-bg rounded-20'
    >
      <div className='pt-14.5 flex flex-col h-full'>
        <h2 className='mb-9 typo-28b text-white'>선호하는 가수 수정하기</h2>

        <div className='mx-auto flex flex-1 flex-col gap-6 min-w-120.5 w-fit overflow-y-hidden'>
          <InputField
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder='가수 이름을 입력해주세요'
          />

          <div className='grid grid-cols-3 gap-4 overflow-y-auto scrollbar-hide'>
            {displayedArtists.map((artist) => (
              <ArtistCard
                key={artist.id}
                artist={artist}
                isSelected={selectedArtists.has(artist.id)}
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
