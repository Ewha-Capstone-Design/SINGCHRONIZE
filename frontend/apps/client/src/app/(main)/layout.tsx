import { Sidebar } from '@/shared/components';

const MainLayout = ({ children }: { children: React.ReactNode }) => {
  return (
    <div className='flex h-full overflow-hidden'>
      <aside className='shrink-0'>
        <Sidebar />
      </aside>

      <main className='flex-1 overflow-y-auto scrollbar-hide'>{children}</main>
    </div>
  );
};

export default MainLayout;
