'use client';

import { forwardRef, useLayoutEffect, useRef } from 'react';
import { cn } from '../../lib/utils';

type TextAreaFieldProps = Omit<
  React.TextareaHTMLAttributes<HTMLTextAreaElement>,
  'size'
> & {
  minRows?: number; // 최소 줄 수
  maxRows?: number; // 최대 줄 수
};

const getLineHeightPx = (el: HTMLTextAreaElement) => {
  const lineHeight = window.getComputedStyle(el).lineHeight;
  const parsed = Number.parseFloat(lineHeight);
  return Number.isFinite(parsed) ? parsed : 24; // fallback
};

const TextAreaField = forwardRef<HTMLTextAreaElement, TextAreaFieldProps>(
  ({ className, onChange, value, defaultValue, minRows = 1, maxRows, ...props }, ref) => {
    const innerRef = useRef<HTMLTextAreaElement | null>(null);

    const setRefs = (node: HTMLTextAreaElement | null) => {
      innerRef.current = node;

      if (typeof ref === 'function') ref(node);
      else if (ref) ref.current = node;
    };

    const resize = (el: HTMLTextAreaElement) => {
      el.style.height = 'auto';

      const lineHeight = getLineHeightPx(el);
      const minHeight = lineHeight * minRows;

      let nextHeight = Math.max(el.scrollHeight, minHeight);

      if (typeof maxRows === 'number') {
        const maxHeight = lineHeight * maxRows;
        nextHeight = Math.min(nextHeight, maxHeight);
        el.style.overflowY = el.scrollHeight > maxHeight ? 'auto' : 'hidden';
      } else {
        el.style.overflowY = 'hidden';
      }

      el.style.height = `${nextHeight}px`;
    };

    useLayoutEffect(() => {
      const el = innerRef.current;
      if (!el) return;
      resize(el);
    }, [value, defaultValue, minRows, maxRows]);

    return (
      <div className={cn('px-6 py-4 flex w-full items-start rounded-10 bg-gray-800')}>
        <textarea
          {...props}
          ref={setRefs}
          value={value as any}
          defaultValue={defaultValue}
          onChange={(e) => {
            resize(e.currentTarget);
            onChange?.(e);
          }}
          className={cn(
            'w-full border-none bg-transparent outline-none resize-none overflow-hidden',
            'typo-16r text-gray-100',
            'placeholder:text-gray-500',
            'caret-gray-100',
            className
          )}
        />
      </div>
    );
  }
);

TextAreaField.displayName = 'TextAreaField';

export default TextAreaField;
