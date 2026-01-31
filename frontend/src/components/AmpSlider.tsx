import React from 'react';
import { SummarySize } from '../types';

interface AmpSliderProps {
  value: SummarySize;
  onChange: (size: SummarySize) => void;
  disabled?: boolean;
}

export const AmpSlider: React.FC<AmpSliderProps> = ({ value, onChange, disabled }) => {
  const options = [SummarySize.SHORT, SummarySize.MEDIUM, SummarySize.LONG];

  const getPosition = () => {
    switch (value) {
      case SummarySize.SHORT: return '0%';
      case SummarySize.MEDIUM: return '50%';
      case SummarySize.LONG: return '100%';
    }
  };

  return (
    <div className="my-8 relative w-full select-none">
      {/* Label */}
      <div className="mb-2 font-marker text-xl uppercase tracking-widest text-black transform -rotate-1">
        Depth Level
      </div>

      {/* Track */}
      <div className="h-6 bg-gray-300 border-4 border-black relative rounded-none flex items-center px-2">
        {/* Ticks */}
        <div className="absolute left-0 w-full h-full flex justify-between items-center px-4 pointer-events-none">
          <div className="w-1 h-3 bg-black/30"></div>
          <div className="w-1 h-3 bg-black/30"></div>
          <div className="w-1 h-3 bg-black/30"></div>
        </div>

        {/* The Lever/Handle */}
        <div
          className="absolute top-1/2 w-8 h-12 bg-yellow-400 border-4 border-black cursor-pointer shadow-[4px_4px_0px_0px_rgba(0,0,0,1)] transition-all duration-300 ease-out z-10"
          style={{
            left: `calc(${getPosition()} - 16px)`, // Center the 32px handle (w-8)
            transform: 'translateY(-50%)'
          }}
        />

        {/* Click Areas */}
        <div className="absolute inset-0 flex w-full h-full z-20">
          {options.map((option) => (
            <div
              key={option}
              onClick={() => !disabled && onChange(option)}
              className="flex-1 cursor-pointer"
              title={option}
            />
          ))}
        </div>
      </div>

      {/* Labels below track */}
      <div className="flex justify-between mt-3 font-terminal text-lg font-bold uppercase">
        {options.map((opt) => (
          <span
            key={opt}
            className={`cursor-pointer transition-colors duration-200 ${value === opt ? 'text-purple-900 underline decoration-4 decoration-yellow-400' : 'text-gray-500'}`}
            onClick={() => !disabled && onChange(opt)}
          >
            {opt}
          </span>
        ))}
      </div>
    </div>
  );
};