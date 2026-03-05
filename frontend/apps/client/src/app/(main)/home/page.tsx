import { cn } from '@/shared/lib/cn';
import {
  ArchivePreview,
  HomeHeader,
  WeeklyChart,
  SimilarVocalSection,
} from '@/widgets/home/ui';
import { VocalAnalysisBanner } from '@/widgets/vocal-analyze/ui';

const HomePage = () => {
  return (
    <main>
      <HomeHeader />

      <div
        className={cn(
          'px-9 pb-9 grid gap-9',
          'grid-cols-1',
          'lg:grid-cols-[minmax(0,1fr)_340px]',
          'xl:grid-cols-[minmax(0,1fr)_400px]'
        )}
      >
        <div className='flex flex-col gap-8 min-w-0'>
          <VocalAnalysisBanner size='compact' />
          <SimilarVocalSection />
          {/* TODO: 라이브 기능 디자인 위치 */}
        </div>

        <div className='flex flex-col gap-12'>
          <WeeklyChart />
          <ArchivePreview />
        </div>
      </div>
    </main>
  );
};

export default HomePage;
