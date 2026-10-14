import React from 'react';
import { cn } from '../utils/cn';

interface BadgeProps {
  children: React.ReactNode;
  variant?: 'pass' | 'warning' | 'fail' | 'danger' | 'critical' | 'high' | 'medium' | 'low' | 'neutral';
  size?: 'sm' | 'md';
  className?: string;
}

export const Badge: React.FC<BadgeProps> = ({
  children,
  variant = 'neutral',
  size = 'md',
  className,
}) => {
  const baseStyles = 'inline-flex items-center font-medium rounded-full';

  const variants = {
    pass: 'bg-emerald-50 text-emerald-700 border border-emerald-200/80',
    warning: 'bg-amber-50 text-amber-700 border border-amber-200/80',
    fail: 'bg-rose-50 text-rose-700 border border-rose-200/80',
    danger: 'bg-rose-50 text-rose-700 border border-rose-200/80',
    critical: 'bg-purple-50 text-purple-700 border border-purple-200/80',
    high: 'bg-rose-50 text-rose-700 border border-rose-200/80',
    medium: 'bg-amber-50 text-amber-700 border border-amber-200/80',
    low: 'bg-blue-50 text-blue-700 border border-blue-200/80',
    neutral: 'bg-slate-100 text-slate-700 border border-slate-200',
  };

  const sizes = {
    sm: 'px-2 py-0.5 text-xs',
    md: 'px-2.5 py-1 text-xs',
  };

  return (
    <span className={cn(baseStyles, variants[variant], sizes[size], className)}>
      {children}
    </span>
  );
};
