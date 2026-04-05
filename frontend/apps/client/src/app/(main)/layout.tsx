import { Sidebar } from '@/shared/components';
import { ProtectedLayout } from '@/shared/auth';

const MainLayout = ({ children }: { children: React.ReactNode }) => {
  return (
    <ProtectedLayout>
      <div className='flex h-full overflow-hidden'>
        <aside className='shrink-0'>
          <Sidebar />
        </aside>

        <main className='flex-1 overflow-y-auto scrollbar-hide'>{children}</main>
      </div>
    </ProtectedLayout>
  );
};

export default MainLayout;
