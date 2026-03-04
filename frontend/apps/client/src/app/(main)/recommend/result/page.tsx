import { VocalReportWidget } from '@/widgets/vocal-report/ui';

import { MOCK_VOCAL_REPORT } from '@/entities/vocal-report/model/mock';

const RecommendResultPage = () => {
  return (
    <div className='p-20'>
      <VocalReportWidget report={MOCK_VOCAL_REPORT} />
    </div>
  );
};

export default RecommendResultPage;
