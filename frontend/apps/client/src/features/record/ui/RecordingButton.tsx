import { Tooltip, TooltipContent, TooltipTrigger } from '@singchronize/ui';
import { RecordingVariant } from '@/shared/types/recommend';
import {
  IcRecordingDone,
  IcRecordingPause,
  IcRecordingStart,
} from '@/shared/assets/icons';

type RecordingButtonProps = {
  variant: RecordingVariant;
  onClick?: () => void;
  className?: string;
};

const RecordingButton = ({ variant, onClick, className }: RecordingButtonProps) => {
  const base =
    'flex items-center justify-center w-[70] h-[70] rounded-full cursor-pointer outlint-none';

  const variantStyles: Record<RecordingVariant, string> = {
    start: 'bg-brand hover:bg-yellow-700 active:bg-yellow-900',
    pause: 'bg-white hover:bg-gray-200 active:bg-gray-400',
    done: 'bg-accent-500 hover:bg-accent-600 active:bg-accent-900',
  };

  const icons = {
    start: <IcRecordingStart />,
    pause: <IcRecordingPause />,
    done: <IcRecordingDone />,
  };

  const labels: Record<RecordingVariant, string> = {
    start: '노래 부르기',
    pause: '잠깐 멈추기',
    done: '끝내기',
  };

  const classes = [base, variantStyles[variant], className ?? ''].join(' ');

  const button = (
    <button
      type='button'
      onClick={onClick}
      className={classes}
      aria-label={labels[variant]}
    >
      {icons[variant]}
    </button>
  );

  return (
    <Tooltip>
      <TooltipTrigger asChild>{button}</TooltipTrigger>
      <TooltipContent>{labels[variant]}</TooltipContent>
    </Tooltip>
  );
};

export default RecordingButton;
