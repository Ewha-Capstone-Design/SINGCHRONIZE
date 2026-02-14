import SegmentedProgress from './SegmentedProgress';
import { IcBack } from '@/shared/assets/icons';
import { RecommendStep, FILLED_COUNT_BY_STEP } from '@/shared/types/recommend';

type FlowHeaderProps = {
  step: RecommendStep;
  onBack: () => void;
};

const FlowHeader = ({ step, onBack }: FlowHeaderProps) => {
  const filled = FILLED_COUNT_BY_STEP[step];

  return (
    <div className='pt-10 px-9 flex flex-col gap-10'>
      <SegmentedProgress filled={filled} />
      <IcBack onClick={onBack} />
    </div>
  );
};

export default FlowHeader;
