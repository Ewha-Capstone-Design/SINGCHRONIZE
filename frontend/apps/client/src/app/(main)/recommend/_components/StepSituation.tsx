'use client';

import { useState } from 'react';

import { Button } from '@singchronize/ui';
import { SituationCard } from '@/shared/components';
import { MAX_SITUATION_SELECT, SITUATION_KEYS } from '@/shared/constants/situation';
import type { SituationKey } from '@/shared/types/category';

type StepSituationProps = {
  onNext: () => void;
};

const StepSituation = ({ onNext }: StepSituationProps) => {
  const [selectedKeys, setSelectedKeys] = useState<SituationKey[]>([]);

  const toggleSelect = (key: SituationKey) => {
    setSelectedKeys((prev) => {
      const isSelected = prev.includes(key);

      if (isSelected) {
        return prev.filter((value) => value !== key);
      }

      if (prev.length >= MAX_SITUATION_SELECT) {
        return prev;
      }

      return [...prev, key];
    });
  };

  return (
    <div className='mt-[4vh] mb-[8vh] flex flex-col justify-center h-full'>
      <div className='flex flex-col gap-[6vh] justify-between items-center max-h-171.5 h-full'>
        <div className='flex flex-col items-center text-center gap-[7]'>
          <p className='typo-32b text-white'>주로 노래 부르는 상황을 골라주세요</p>
          <p className='typo-20r text-gray-300'>
            최대 4개까지 선택 가능해요. 없으면 건너뛰어도 돼요
          </p>
        </div>

        <div className='grid grid-cols-4 gap-5'>
          {SITUATION_KEYS.map((key) => (
            <SituationCard
              key={key}
              situationKey={key}
              isSelected={selectedKeys.includes(key)}
              onClick={() => toggleSelect(key)}
            />
          ))}
        </div>

        <Button variant='normal' onClick={onNext}>
          선택 완료하기
        </Button>
      </div>
    </div>
  );
};

export default StepSituation;
