import React from 'react';

interface BrutalistButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'success' | 'danger';
  size?: 'sm' | 'md' | 'lg';
  isLoading?: boolean;
  children: React.ReactNode;
}

export const BrutalistButton: React.FC<BrutalistButtonProps> = ({
  variant = 'primary',
  size = 'md',
  isLoading = false,
  children,
  className = '',
  disabled,
  ...props
}) => {
  const baseStyles = `
    font-marker text-xl brutalist-border transition-all duration-200
    brutalist-shadow hover:translate-y-1 hover:shadow-none
    active:translate-y-1 disabled:cursor-not-allowed disabled:opacity-50
    flex items-center justify-center gap-2
  `;

  const variantStyles = {
    primary: 'bg-white hover:bg-gray-100',
    secondary: 'bg-yellow-400',
    success: 'bg-green-400',
    danger: 'bg-red-500 text-white hover:bg-red-700',
  };

  const sizeStyles = {
    sm: 'px-3 py-1 text-lg',
    md: 'px-6 py-3 text-xl',
    lg: 'px-8 py-4 text-2xl',
  };

  return (
    <button
      className={`${baseStyles} ${variantStyles[variant]} ${sizeStyles[size]} ${className}`}
      disabled={disabled || isLoading}
      {...props}
    >
      {isLoading ? 'PROCESSING...' : children}
    </button>
  );
};

// Specialized button for the main action (Extract)
interface ExtractButtonProps {
  onClick: () => void;
  isLoading: boolean;
  disabled?: boolean;
}

export const ExtractButton: React.FC<ExtractButtonProps> = ({ onClick, isLoading, disabled }) => {
  return (
    <button
      onClick={onClick}
      disabled={disabled || isLoading}
      className={`
        relative group
        px-12 py-4 bg-yellow-400 brutalist-border
        font-marker text-3xl uppercase tracking-wider
        shadow-[6px_6px_0px_0px_#000] 
        hover:translate-x-1 hover:translate-y-1 hover:shadow-[2px_2px_0px_0px_#000]
        active:translate-x-2 active:translate-y-2 active:shadow-none
        transition-all duration-150
        disabled:opacity-50 disabled:cursor-not-allowed
        brutalist-transform hover:rotate-0
      `}
    >
      {isLoading ? 'EXTRACTING...' : 'EXTRACT'}
      {/* Decorative burst effect on hover */}
      <span className="absolute -top-2 -right-2 w-4 h-4 bg-red-500 border-2 border-black opacity-0 group-hover:opacity-100 transition-opacity" />
      <span className="absolute -bottom-2 -left-2 w-3 h-3 bg-blue-500 border-2 border-black opacity-0 group-hover:opacity-100 transition-opacity" />
    </button>
  );
};