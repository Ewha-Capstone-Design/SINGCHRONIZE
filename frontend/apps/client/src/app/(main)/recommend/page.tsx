'use client';

import { VocalAnalysisBanner } from '@/widgets/vocal-analyze/ui';
import { VocalReportWidget } from '@/widgets/vocal-report/ui';

import { useVocalProfile } from '@/entities/analysis';

const RecommendPage = () => {
  const { data: report } = useVocalProfile();

  return (
    <div>
      <VocalAnalysisBanner size='recommend' />
      {report?.updated_at && (
        <div className='py-12 px-[10vw] flex flex-col gap-6'>
          <div className='mx-auto'>
            <h2 className='typo-28b text-gray-100'>나의 보컬 리포트</h2>
            {report.updated_at && (
              <p className='typo-14r text-gray-500'>최근 업데이트 {report.updated_at}</p>
            )}
          </div>
          <VocalReportWidget desktopLayout='wide' report={report} />
        </div>
      )}
    </div>
  );
};

export default RecommendPage;
