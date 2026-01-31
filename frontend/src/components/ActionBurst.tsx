import React from 'react';

interface ActionBurstProps {
  onClick: () => void;
  isLoading: boolean;
  text: string;
}

export const ActionBurst: React.FC<ActionBurstProps> = ({ onClick, isLoading, text }) => {
  return (
    <div className="relative group flex justify-center items-center p-8">
      {/* Lightning bolts decorative */}
      <div className="absolute -left-4 top-0 text-4xl text-black font-marker animate-pulse hidden group-hover:block select-none">ZAP!</div>
      <div className="absolute -right-4 bottom-0 text-4xl text-black font-marker animate-pulse delay-75 hidden group-hover:block select-none">POW!</div>

      <button
        onClick={onClick}
        disabled={isLoading}
        className={`
            relative w-64 h-32 
            bg-yellow-400 hover:bg-yellow-300 active:bg-yellow-500
            text-black font-marker text-4xl tracking-widest
            transition-transform duration-100
            hover:scale-110 hover:rotate-2
            active:scale-95 active:-rotate-2
            flex items-center justify-center
            clip-explosion
            disabled:opacity-70 disabled:grayscale
            disabled:cursor-not-allowed
          `}
        style={{
          filter: 'drop-shadow(8px 8px 0px #000)',
        }}
      >
        <span className={`${isLoading ? 'animate-bounce' : ''} z-10 relative`}>
          {isLoading ? 'PROCESSING...' : text}
        </span>

        {/* Inner cracks/lines */}
        <div className="absolute inset-0 bg-[url('https://www.transparenttextures.com/patterns/cracked-concrete.png')] opacity-20 mix-blend-multiply"></div>
      </button>
    </div>
  );
};