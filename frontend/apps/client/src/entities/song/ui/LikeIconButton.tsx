import { IcHeartOff, IcHeartOn } from '@/shared/assets/icons';

type LikeIconButtonProps = {
  isLiked: boolean;
  onClick?: () => void;
  disabled?: boolean;
};

const LikeIconButton = ({ isLiked, onClick, disabled }: LikeIconButtonProps) => {
  return (
    <button
      type='button'
      aria-label={isLiked ? '좋아요 취소' : '좋아요'}
      aria-pressed={isLiked}
      onClick={onClick}
      disabled={disabled}
      className='inline-flex items-center justify-center'
    >
      {isLiked ? <IcHeartOn /> : <IcHeartOff />}
    </button>
  );
};

export default LikeIconButton;
