import * as React from 'react';
import { Slot } from '@radix-ui/react-slot';
import { cva, type VariantProps } from 'class-variance-authority';

import { cn } from '../../lib/utils';

const buttonVariants = cva(
  'inline-flex items-center justify-center gap-[10px] px-6 py-[10px] rounded-full typo-18sb text-center shrink-0 transition-colors cursor-pointer disabled:pointer-events-none',
  {
    variants: {
      variant: {
        primary: '',
        normal: '',
        outline: '',
        accent: '',
      },
      state: {
        enabled: '',
        disabled: 'bg-gray-700 text-gray-500',
      },
    },
    compoundVariants: [
      // PRIMARY
      {
        variant: 'primary',
        state: 'enabled',
        className: 'bg-brand text-black hover:bg-yellow-700 active:bg-yellow-900',
      },
      // NORMAL
      {
        variant: 'normal',
        state: 'enabled',
        className: 'bg-white text-black hover:bg-gray-200 active:bg-gray-400',
      },
      // OUTLINE
      {
        variant: 'outline',
        state: 'enabled',
        className:
          'border border-gray-500 text-white hover:border-white active:border-gray-500 active:text-gray-500',
      },
      // ACCENT
      {
        variant: 'accent',
        state: 'enabled',
        className:
          'bg-accent-500 text-white hover:bg-accent-600 active:bg-accent-900 active:text-gray-400',
      },
    ],
    defaultVariants: {
      variant: 'primary',
      state: 'enabled',
    },
  }
);

export interface ButtonProps
  extends
    React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean;
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, asChild = false, disabled, ...props }, ref) => {
    const Comp = asChild ? Slot : 'button';

    return (
      <Comp
        ref={ref}
        disabled={disabled}
        className={cn(
          buttonVariants({
            variant,
            state: disabled ? 'disabled' : 'enabled',
            className,
          })
        )}
        {...props}
      />
    );
  }
);

Button.displayName = 'Button';

export default Button;
