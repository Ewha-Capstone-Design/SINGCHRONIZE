'use client';

import { VocalAnalysisBanner } from '@/widgets/vocal-analyze/ui';
import { VocalReportWidget } from '@/widgets/vocal-report/ui';

import { MOCK_VOCAL_REPORT } from '@/entities/vocal-report/model/mock';

const RecommendPage = () => {
  return (
    <div>
      <VocalAnalysisBanner size='wide' />
      <div className='py-12 px-[10vw] flex flex-col gap-6'>
        <div className='mx-auto'>
          <h2 className='typo-28b text-gray-100'>나의 보컬 리포트</h2>
          <p className='typo-14r text-gray-500'>최근 업데이트 2026.02.03</p>
        </div>
        <VocalReportWidget desktopLayout='wide' report={MOCK_VOCAL_REPORT} />
      </div>
    </div>
  );
};

export default RecommendPage;
