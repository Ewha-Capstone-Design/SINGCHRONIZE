'use client';

import { PageHeader } from '@/shared/components';
import { VocalReportWidget } from '@/widgets/vocal-report/ui';

import { useVocalProfile } from '@/entities/analysis';

const VocalReportPage = () => {
  const { data: report } = useVocalProfile();

  if (!report) return null;

  return (
    <div className='py-13 flex flex-col gap-10'>
      <PageHeader
        title='나의 보컬 리포트'
        subText={report.updated_at ? `최근 업데이트 ${report.updated_at}` : undefined}
      />
      <div className='mx-auto w-226'>
        <VocalReportWidget desktopLayout='wide' report={report} />
      </div>
    </div>
  );
};

export default VocalReportPage;
