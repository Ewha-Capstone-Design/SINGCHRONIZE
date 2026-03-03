import { cn } from '@/shared/lib/cn';

const LoginLayout = ({ children }: { children: React.ReactNode }) => {
  return (
    <div className='relative w-full min-h-dvh text-white'>
      <div
        className={cn(
          'pointer-events-none absolute inset-0 overflow-hidden',
          'bg-bg bg-no-repeat',
          'bg-[radial-gradient(50%_50%_at_50%_50%,rgba(200,255,0,0.20)_0%,rgba(22,22,22,0.20)_100%)]',
          'bg-size-[100%_150%]',
          'bg-position-[50%_-30%]'
        )}
      />
      <div className='relative py-[13vh] flex justify-center w-full min-h-dvh'>
        {children}
      </div>
    </div>
  );
};

export default LoginLayout;
