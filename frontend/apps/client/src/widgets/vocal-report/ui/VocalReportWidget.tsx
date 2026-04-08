import type { VocalReport } from '@/entities/vocal-report';
import { cn } from '@/shared/lib/cn';
import VocalTraitsRadarCard from './cards/VocalTraitsRadarCard';
import GenreFitCard from './cards/GenreFitCard';
import TimbreBarsCard from './cards/TimbreBarsCard';
import RangeAnalysisCard from './cards/RangeAnalysisCard';

import { useMe } from '@/entities/user';

type DesktopLayout = 'grid' | 'wide';

type VocalReportWidgetProps = {
  report: VocalReport;
  desktopLayout?: DesktopLayout;
};

const VocalReportWidget = ({
  report,
  desktopLayout = 'wide',
}: VocalReportWidgetProps) => {
  const isGrid = desktopLayout === 'grid';

  const { data: me } = useMe();
  const nickname = me?.nickname ?? '사용자';

  return (
    <div
      className={cn(
        'grid grid-cols-1 gap-6',
        isGrid
          ? 'lg:grid-cols-3 lg:grid-rows-2 lg:grid-flow-col'
          : 'lg:grid-cols-2 lg:grid-flow-row',
      )}
    >
      <VocalTraitsRadarCard data={report.traits} />

      <TimbreBarsCard data={report.timbre} />

      <div className='lg:col-span-2'>
        <GenreFitCard
          data={report.genreFit.data}
          bestGenre={report.genreFit.bestGenre}
          nickname={nickname}
        />
      </div>

      <div className='lg:col-span-2'>
        <RangeAnalysisCard
          data={report.range.data}
          comfort={report.range.comfort}
          stats={report.range.stats}
          nickname={nickname}
        />
      </div>
    </div>
  );
};

export default VocalReportWidget;
