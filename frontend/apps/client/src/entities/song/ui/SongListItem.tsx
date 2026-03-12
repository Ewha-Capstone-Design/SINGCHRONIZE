'use client';

import { cn } from '@/shared/lib/cn';
import { LikeIconButton, MoreActionButton } from '.';

type ListVariant = 'list2' | 'list3' | 'list4' | 'list5';

interface SongListItemProps {
  variant: ListVariant;

  rank?: number;
  thumbnail?: string;
  title: string;
  artist: string;

  // list2
  tag?: string;
  bpm?: number;
  musicKey?: string;

  // list2, list5
  matchRate?: number;

  // list4
  likeCount?: number;

  // list3
  rightSlot?: React.ReactNode;

  // ui state
  isLiked?: boolean;

  // actions
  onLikeClick?: () => void;
  onMoreClick?: () => void;
}

const SongListItem = ({
  variant,
  rank,
  thumbnail,
  title,
  artist,
  tag,
  bpm,
  musicKey,
  matchRate,
  likeCount,
  rightSlot,
  isLiked = false,
  onLikeClick,
  onMoreClick,
}: SongListItemProps) => {
  const showRank = variant === 'list2' || variant === 'list4' || variant === 'list5';
  const isTall = variant === 'list2' || variant === 'list3'; // 90
  const showMatchRate =
    (variant === 'list2' || variant === 'list5') && matchRate !== undefined;

  const handleLikeClick = () => {
    onLikeClick?.();
  };

  const handleMoreClick = () => {
    onMoreClick?.();
  };

  return (
    <div
      className={cn(
        'px-5 flex items-center gap-4 w-full rounded-10 bg-gray-800 shrink-0',
        isTall ? 'h-22.5' : 'h-20'
      )}
    >
      {/* [왼쪽] 순위/번호 - list2,4,5 */}
      {showRank && (
        <span className='w-5 shrink-0 text-center typo-18sb text-gray-200'>
          {rank ?? '-'}
        </span>
      )}

      {/* [중앙] 앨범 커버 이미지 */}
      <div className='relative size-13.5 shrink-0 overflow-hidden rounded-10 bg-gray-700'>
        {thumbnail ? (
          <img src={thumbnail} alt={title} className='size-full object-cover' />
        ) : (
          <div className='size-full bg-white-10' />
        )}
      </div>

      {/* [중앙] 곡 정보 */}
      <div className='flex min-w-0 flex-1 flex-col gap-0.5 text-left'>
        <h4 className='truncate typo-18sb text-white'>{title}</h4>
        <p className='truncate typo-14r text-gray-200'>{artist}</p>
      </div>

      {/* [오른쪽] 메타 영역 */}
      <div className='flex items-center gap-4'>
        {/* list2 */}
        {variant === 'list2' && (
          <>
            {tag && (
              <span className='rounded-10 bg-gray-700 px-3 py-1 typo-14r text-gray-300'>
                {tag}
              </span>
            )}

            <div className='flex flex-col items-center gap-1'>
              <span className='typo-14r text-gray-500'>BPM</span>
              <span className='typo-14r text-gray-200'>{bpm ?? '-'}</span>
            </div>

            <div className='flex flex-col items-center gap-1'>
              <span className='typo-14r text-gray-500'>Key</span>
              <span className='typo-14r text-gray-200'>{musicKey ?? '-'}</span>
            </div>
          </>
        )}

        {/* list2, list5: 일치율 */}
        {showMatchRate && (
          <div className='flex h-9.5 items-center rounded-10 border border-gray-600 px-3 typo-14r text-gray-100'>
            {matchRate}%
          </div>
        )}

        {/* list4: 좋아요 수 */}
        {variant === 'list4' && (
          <div className='flex items-center gap-1.25'>
            <LikeIconButton isLiked={isLiked} onClick={handleLikeClick} />
            <span className='typo-16b text-gray-200'>{likeCount ?? 0}</span>
          </div>
        )}
      </div>

      {/* [오른쪽] 액션 영역 */}
      {variant !== 'list4' && (
        <div className='flex items-center'>
          {/* list3: 하트 + 더보기 */}
          {variant === 'list3' ? (
            rightSlot ? (
              <div className='flex items-center'>{rightSlot}</div>
            ) : (
              <div className='flex items-center gap-4'>
                <LikeIconButton isLiked={isLiked} onClick={handleLikeClick} />
                <MoreActionButton onClick={handleMoreClick} />
              </div>
            )
          ) : null}

          {/* list2, list5: 하트 */}
          {variant === 'list2' || variant === 'list5' ? (
            <LikeIconButton isLiked={isLiked} onClick={handleLikeClick} />
          ) : null}
        </div>
      )}
    </div>
  );
};

export default SongListItem;
