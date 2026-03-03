import {
  ArchivePreview,
  HomeHeader,
  VocalAnalysisBanner,
  WeeklyChart,
} from '@/widgets/home/ui';

const HomePage = () => {
  return (
    <main>
      <HomeHeader />

      <div className='px-9 pb-9 grid grid-cols-[1fr_400px] gap-9'>
        <div className='flex flex-col gap-8'>
          <VocalAnalysisBanner />
          {/* 라이브 기능 디자인 위치 */}
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
