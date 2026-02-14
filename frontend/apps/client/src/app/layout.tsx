import './global.css';
import { TooltipProvider } from '@singchronize/ui';

const RootLayout = ({ children }: { children: React.ReactNode }) => {
  return (
    <html lang='ko'>
      <body>
        <TooltipProvider delayDuration={0}>{children}</TooltipProvider>
      </body>
    </html>
  );
};

export default RootLayout;
