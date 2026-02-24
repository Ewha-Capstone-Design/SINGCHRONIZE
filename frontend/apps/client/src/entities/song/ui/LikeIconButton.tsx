import { IcHeartOff, IcHeartOn } from '@/shared/assets/icons';

type LikeIconButtonProps = {
  isLiked: boolean;
  onClick: (e: React.MouseEvent<HTMLButtonElement>) => void;
};

const LikeIconButton = ({ isLiked, onClick }: LikeIconButtonProps) => {
  return (
    <button
      type='button'
      aria-label={isLiked ? '좋아요 취소' : '좋아요'}
      aria-pressed={isLiked}
      onClick={onClick}
      className='inline-flex items-center justify-center'
    >
      {isLiked ? <IcHeartOn /> : <IcHeartOff />}
    </button>
  );
};

export default LikeIconButton;
