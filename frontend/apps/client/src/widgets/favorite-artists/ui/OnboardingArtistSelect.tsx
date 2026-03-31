'use client';

import { useCallback, useEffect, useState } from 'react';
import { Button } from '@singchronize/ui';
import { cn } from '@/shared/lib/cn';
import { IcRefresh } from '@/shared/assets/icons';

import { ArtistUiType, ArtistIdType, GenderType } from '@/entities/artist/model/types';
import ArtistCard from '@/entities/artist/ui/ArtistCard';
import { useMultiSelectIds } from '../model/useMultiSelectIds';
import { validateMinSelect } from '../model/validateMinSelect';
import { GenderToggleButton, SelectionCounter } from '.';

import { fetchRecommendedArtists } from '@/entities/artist/model/mock';
import { useOnboardingStep2 } from '@/entities/user';

const MAX_SELECT = 3;

type OnboardingArtistSelectProps = {
  onCompleted?: () => void;
};

const OnboardingArtistSelect = ({ onCompleted }: OnboardingArtistSelectProps) => {
  const { mutateAsync: onboardingStep2 } = useOnboardingStep2();
  const [gender, setGender] = useState<GenderType>('male');
  const [artists, setArtists] = useState<ArtistUiType[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  const { selectedIds, toggle } = useMultiSelectIds({ maxSelect: MAX_SELECT });

  const canConfirm = validateMinSelect(MAX_SELECT, selectedIds.length);

  const loadArtists = useCallback(async (nextGender: GenderType) => {
    setIsLoading(true);
    try {
      const data = await fetchRecommendedArtists(nextGender);
      setArtists(data);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    loadArtists(gender);
  }, [gender, loadArtists]);

  const handleGenderChange = (next: GenderType) => {
    setGender(next);
  };

  const handleRefresh = () => {
    loadArtists(gender);
  };

  const submitSelectedArtists = async (ids: ArtistIdType[]) => {
    await onboardingStep2(ids as number[]);
  };

  const handleConfirm = async () => {
    if (!canConfirm) return;

    submitSelectedArtists(selectedIds);
    onCompleted?.();
  };

  return (
    <section className='w-full'>
      <div className='mb-4 flex items-center justify-start gap-4'>
        <GenderToggleButton value={gender} onChange={handleGenderChange} />

        <button
          type='button'
          onClick={handleRefresh}
          aria-label='새로고침'
          disabled={isLoading}
          className={cn(
            'inline-flex h-8 w-8 items-center justify-center',
            'disabled:opacity-50',
          )}
        >
          <IcRefresh />
        </button>
      </div>

      <div className='grid grid-cols-3 gap-4'>
        {artists.map((artist) => (
          <ArtistCard
            key={artist.id}
            artist={artist}
            isSelected={selectedIds.includes(artist.id)}
            onToggle={toggle}
          />
        ))}
      </div>

      <div className='mt-6 flex flex-col items-center gap-16'>
        <SelectionCounter maxSelect={MAX_SELECT} selectedCount={selectedIds.length} />
        <Button variant='primary' disabled={!canConfirm} onClick={handleConfirm}>
          선택 완료하기
        </Button>
      </div>
    </section>
  );
};

export default OnboardingArtistSelect;
