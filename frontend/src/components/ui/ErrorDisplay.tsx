import React from 'react';

interface ErrorDisplayProps {
  error: string;
  className?: string;
}

export const ErrorDisplay: React.FC<ErrorDisplayProps> = ({ error, className = '' }) => {
  if (!error) return null;

  return (
    <div className={`my-4 p-3 bg-red-100 border-l-8 border-red-600 font-terminal text-xl text-red-700 font-bold animate-pulse ${className}`}>
      ERROR: {error}
    </div>
  );
};