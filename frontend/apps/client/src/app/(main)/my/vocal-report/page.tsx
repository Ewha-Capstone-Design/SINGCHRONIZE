import { PageHeader } from '@/shared/components';
import { VocalReportWidget } from '@/widgets/vocal-report/ui';

import { MOCK_VOCAL_REPORT } from '@/entities/vocal-report/model/mock';

const VocalReportPage = () => {
  return (
    <div className='py-13 flex flex-col gap-10'>
      <PageHeader
        title='나의 보컬 리포트'
        subText={`최근 업데이트 ${MOCK_VOCAL_REPORT.updated_at}`}
      />
      <div className='mx-auto w-226'>
        <VocalReportWidget desktopLayout='wide' report={MOCK_VOCAL_REPORT} />
      </div>
    </div>
  );
};

export default VocalReportPage;
