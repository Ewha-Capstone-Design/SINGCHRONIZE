'use client';

import { useState, forwardRef } from 'react';
import { cn } from '../../lib/utils';

type InputStatus = 'default' | 'error';

interface InputFieldProps extends Omit<
  React.InputHTMLAttributes<HTMLInputElement>,
  'size'
> {
  message?: string;
  status?: InputStatus;
}

const InputField = forwardRef<HTMLInputElement, InputFieldProps>(
  (
    { message, status = 'default', disabled, className, onFocus, onBlur, ...props },
    ref
  ) => {
    const [isFocused, setIsFocused] = useState(false);
    const isError = status === 'error';

    const containerStyles = cn(
      'px-5 py-3 flex w-full items-center rounded-10 border bg-transparent transition-all duration-200',
      // Default
      'border-gray-300',
      // Focus
      isFocused && !isError && 'border-brand',
      // Error
      isError && 'border-accent-500'
    );

    return (
      <div className='flex flex-col gap-2 w-full'>
        <div className={containerStyles}>
          <input
            {...props}
            ref={ref}
            aria-invalid={isError}
            onFocus={(e) => {
              setIsFocused(true);
              onFocus?.(e);
            }}
            onBlur={(e) => {
              setIsFocused(false);
              onBlur?.(e);
            }}
            className={cn(
              'w-full border-none bg-transparent outline-none',
              'typo-20r text-white caret-brand',
              'placeholder:text-gray-600',
              className
            )}
          />
        </div>

        {message && (
          <p
            className={cn(
              'typo-14r transition-colors duration-200',
              isError ? 'text-accent-500' : 'text-gray-500'
            )}
          >
            {message}
          </p>
        )}
      </div>
    );
  }
);

InputField.displayName = 'InputField';

export default InputField;
