'use client';

import { cn } from '@/shared/lib/cn';
import { IcPlay } from '@/shared/assets/icons';
import { AppImage } from '@/shared/components';
import { BuskingType, BuskingUiType } from '@/entities/busking/model/types';

type BuskingCardVariant = 'sm' | 'md' | 'lg';

interface BuskingCardProps {
  variant?: BuskingCardVariant;
  item: BuskingUiType;
  onClick?: () => void;
}

const variantClassMap: Record<BuskingCardVariant, string> = {
  sm: 'w-[192px] h-[153px]',
  md: 'w-[350px] h-[222px]',
  lg: 'w-[530px] h-[300px]',
};

const badgeVariantClassMap: Record<BuskingCardVariant, string> = {
  sm: 'px-[10.6px] py-[3.5px] rounded-[9px] typo-12r',
  md: 'px-[15.5px] py-[5px] rounded-[13px] typo-16m',
  lg: 'px-[15.5px] py-[5px] rounded-[13px] typo-18sb',
};

const badgeClassMap: Record<BuskingType, string> = {
  live: 'bg-accent-600 text-white',
  record: 'bg-brand text-black',
};

const badgeTextMap: Record<BuskingType, string> = {
  live: 'Live',
  record: 'Record',
};

const profileSizeMap: Record<BuskingCardVariant, string> = {
  sm: 'size-7',
  md: 'size-10',
  lg: 'size-14',
};

const profileGapMap: Record<BuskingCardVariant, string> = {
  sm: 'gap-2',
  md: 'gap-3',
  lg: 'gap-2',
};

const nicknameTypoMap: Record<BuskingCardVariant, string> = {
  sm: 'typo-12r',
  md: 'typo-16r',
  lg: 'typo-18sb',
};

const listenerTypoMap: Record<BuskingCardVariant, string> = {
  sm: 'typo-12r text-gray-500',
  md: 'typo-14r text-gray-500',
  lg: 'typo-16r text-gray-300',
};

const bottomAreaClassMap: Record<BuskingCardVariant, string> = {
  sm: 'h-12 px-2 bg-gray-800',
  md: 'h-17 px-3 bg-gray-800',
  lg: 'h-23 px-4.5',
};

const BuskingCard = ({ variant = 'md', item, onClick }: BuskingCardProps) => {
  const { status, thumbnail, profileImage, nickname, totalViewers } = item;

  return (
    <button
      type='button'
      onClick={onClick}
      className={cn(
        'relative overflow-hidden rounded-10 bg-gray-800 text-left shrink-0',
        variantClassMap[variant],
      )}
    >
      {/* 배경 썸네일 */}
      <div className='absolute inset-0'>
        <AppImage src={thumbnail} alt={nickname} fill className='object-cover' />
      </div>

      {/* 상단 배지 */}
      <div className='absolute left-2.5 top-2.5 z-10'>
        <span
          className={cn(
            'inline-flex items-center',
            badgeVariantClassMap[variant],
            badgeClassMap[status],
          )}
        >
          {badgeTextMap[status]}
        </span>
      </div>

      {/* 하단 그라디언트 */}
      {variant === 'lg' && (
        <div
          className={cn(
            'absolute inset-x-0 bottom-0 z-1 h-32.5',
            'bg-[linear-gradient(180deg,rgba(0,0,0,0)_0%,rgba(0,0,0,0.5)_60%,rgba(0,0,0,1)_100%)]',
          )}
        />
      )}

      {/* 하단 정보 영역 */}
      <div
        className={cn(
          'absolute inset-x-0 bottom-0 z-10 flex items-end justify-between',
          bottomAreaClassMap[variant],
        )}
      >
        <div className={cn('flex items-center min-w-0 h-full', profileGapMap[variant])}>
          {/* 프로필 */}
          <div
            className={cn(
              'relative shrink-0 overflow-hidden rounded-full bg-white border',
              status === 'live' ? 'border-accent-500' : 'border-brand',
              profileSizeMap[variant],
            )}
          >
            <AppImage src={profileImage} alt={nickname} fill className='object-cover' />
          </div>

          {/* 텍스트 */}
          <div className='min-w-0'>
            <p className={cn('truncate text-white', nicknameTypoMap[variant])}>
              {nickname}
            </p>
            <p className={cn('truncate', listenerTypoMap[variant])}>
              {totalViewers}명이 같이 듣는 중
            </p>
          </div>
        </div>

        {/* 재생 아이콘 */}
        {variant === 'lg' && (
          <div className='pb-4.5 text-gray-200'>
            <IcPlay />
          </div>
        )}
      </div>
    </button>
  );
};

export default BuskingCard;
