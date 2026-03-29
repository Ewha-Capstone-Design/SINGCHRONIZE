import type { Metadata } from 'next';
import { metadataConfig } from './metadata';
import './global.css';
import { Providers } from './providers';
import { TooltipProvider } from '@singchronize/ui';

export const metadata: Metadata = metadataConfig;

const RootLayout = ({ children }: { children: React.ReactNode }) => {
  return (
    <html lang='ko'>
      <body className='h-screen bg-bg scrollbar-hide'>
        <Providers>
          <TooltipProvider delayDuration={0}>{children}</TooltipProvider>
        </Providers>
      </body>
    </html>
  );
};

export default RootLayout;
