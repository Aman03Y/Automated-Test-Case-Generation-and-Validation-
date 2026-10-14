import React from 'react';
import { cn } from '../utils/cn';

interface ProgressBarProps {
  value: number; // 0 to 100
  label?: string;
  showPercentage?: boolean;
  color?: 'blue' | 'emerald' | 'amber' | 'rose' | 'purple';
  height?: 'sm' | 'md' | 'lg';
  className?: string;
}

export const ProgressBar: React.FC<ProgressBarProps> = ({
  value,
  label,
  showPercentage = true,
  color = 'blue',
  height = 'md',
  className,
}) => {
  const boundedValue = Math.max(0, Math.min(100, value));

  const colors = {
    blue: 'bg-blue-600',
    emerald: 'bg-emerald-500',
    amber: 'bg-amber-500',
    rose: 'bg-rose-500',
    purple: 'bg-purple-600',
  };

  const heights = {
    sm: 'h-1.5',
    md: 'h-2.5',
    lg: 'h-4',
  };

  return (
    <div className={cn('w-full', className)}>
      {(label || showPercentage) && (
        <div className="flex justify-between items-center mb-1.5 text-xs font-medium text-slate-700">
          <span>{label}</span>
          {showPercentage && <span>{boundedValue.toFixed(1)}%</span>}
        </div>
      )}
      <div className={cn('w-full bg-slate-200 rounded-full overflow-hidden', heights[height])}>
        <div
          className={cn('h-full transition-all duration-500 rounded-full', colors[color])}
          style={{ width: `${boundedValue}%` }}
        />
      </div>
    </div>
  );
};
