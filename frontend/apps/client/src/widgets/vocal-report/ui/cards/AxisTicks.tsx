'use client';

type AxisTickProps = {
  x?: number;
  y?: number;
  payload?: { value?: string | number };
};

export const XAxisTick = ({ x, y, payload }: AxisTickProps) => {
  const value = payload?.value ?? '';

  return (
    <g transform={`translate(${x ?? 0},${y ?? 0})`}>
      <text
        x={0}
        y={0}
        dy={16}
        textAnchor='middle'
        className='typo-14r fill-(--semantic-chart-axis-strong)'
      >
        {String(value)}
      </text>
    </g>
  );
};

export const YAxisTick = ({ x, y, payload }: AxisTickProps) => {
  const value = payload?.value ?? '';

  return (
    <g transform={`translate(${x ?? 0},${y ?? 0})`}>
      <text
        x={0}
        y={0}
        dx={-8}
        dy={4}
        textAnchor='end'
        className='typo-12r fill-(--semantic-chart-axis)'
      >
        {String(value)}
      </text>
    </g>
  );
};

export type { AxisTickProps };
