'use client';

import { useState } from 'react';

import { Button } from '@singchronize/ui';
import { GenreCard } from '@/shared/components';
import { GENRE_API_LABEL, GENRE_KEYS, MAX_GENRE_SELECT } from '@/shared/constants/genre';
import type { GenreKey } from '@/shared/types/category';

type StepGenreProps = {
  onNext: (selectedLabels: string[]) => void;
  isSubmitting?: boolean;
  submitError?: boolean;
};

const StepGenre = ({
  onNext,
  isSubmitting = false,
  submitError = false,
}: StepGenreProps) => {
  const [selectedKeys, setSelectedKeys] = useState<GenreKey[]>([]);

  const toggleSelect = (key: GenreKey) => {
    setSelectedKeys((prev) => {
      const isSelected = prev.includes(key);

      if (isSelected) {
        return prev.filter((value) => value !== key);
      }

      if (prev.length >= MAX_GENRE_SELECT) {
        return prev;
      }

      return [...prev, key];
    });
  };

  return (
    <div className='mt-[4vh] mb-[8vh] flex h-full flex-col justify-center'>
      <div className='flex h-full max-h-171.5 flex-col items-center justify-between gap-[6vh]'>
        <div className='flex flex-col items-center gap-[7] text-center'>
          <p className='typo-32b text-white'>좋아하는 장르를 선택해 주세요</p>
          <p className='typo-20r text-gray-300'>
            최대 3개까지 선택 가능해요. 없으면 건너뛰어도 돼요
          </p>
        </div>

        <div className='grid grid-cols-3 gap-5'>
          {GENRE_KEYS.map((key) => (
            <GenreCard
              key={key}
              genreKey={key}
              isSelected={selectedKeys.includes(key)}
              onClick={() => toggleSelect(key)}
            />
          ))}
        </div>

        <div className='flex flex-col items-center gap-3'>
          {submitError && (
            <p className='typo-14r text-red-400'>
              제출에 실패했어요. 다시 시도해 주세요.
            </p>
          )}
          <Button
            variant='normal'
            onClick={() => onNext(selectedKeys.map((k) => GENRE_API_LABEL[k]))}
            disabled={isSubmitting}
          >
            선택 완료하기
          </Button>
        </div>
      </div>
    </div>
  );
};

export default StepGenre;
