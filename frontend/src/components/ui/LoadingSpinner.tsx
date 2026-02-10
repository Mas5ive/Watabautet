import React from 'react';
import { Loader2 } from 'lucide-react';

interface LoadingSpinnerProps {
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

export const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({ size = 'md', className = '' }) => {
  const sizeMap = {
    sm: 24,
    md: 40,
    lg: 64,
  };

  const iconSize = sizeMap[size];

  return (
    <div className={`flex justify-center items-center ${className}`}>
      <Loader2 className="animate-spin text-black" style={{ width: iconSize, height: iconSize }} />
    </div>
  );
};

interface LoadingOverlayProps {
  message?: string;
}

export const LoadingOverlay: React.FC<LoadingOverlayProps> = ({ message = 'LOADING...' }) => {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
      <div className="bg-white p-8 brutalist-border shadow-[8px_8px_0px_0px_#000]">
        <LoadingSpinner size="lg" />
        <p className="mt-4 font-marker text-xl text-center">{message}</p>
      </div>
    </div>
  );
};