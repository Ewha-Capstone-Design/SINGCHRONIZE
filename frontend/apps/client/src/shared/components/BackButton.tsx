'use client';

import { IcBack } from '@/shared/assets/icons';
import { useNavigate } from '../lib/navigation';

type BackButtonProps = {
  onClick?: () => void;
  className?: string;
};

const BackButton = ({ onClick, className = 'w-fit' }: BackButtonProps) => {
  const { back } = useNavigate();

  return (
    <button type='button' className={className} onClick={onClick ?? back}>
      <IcBack />
    </button>
  );
};

export default BackButton;
