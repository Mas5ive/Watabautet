import React from 'react';

import mascotPoints from '../pics/mascot_points.png';
import mascotSits from '../pics/mascot_sits.png';

const DEFAULT_DESKTOP = mascotPoints;
const DEFAULT_MOBILE = mascotSits;

interface MascotProps {
  desktopSrc?: string;
  mobileSrc?: string;
}

export const Mascot: React.FC<MascotProps> = ({
  desktopSrc = DEFAULT_DESKTOP,
  mobileSrc = DEFAULT_MOBILE
}) => {
  return (
    <div className="relative w-full h-[500px] md:h-full flex items-end justify-center md:justify-end">
      <div className="relative z-10 w-full h-full flex items-end justify-center md:justify-end transition-transform hover:scale-105 duration-300">
        {/* Responsive Image Switching using Picture element */}
        <picture className="flex items-end justify-center md:justify-end w-full h-full">
          <source media="(min-width: 768px)" srcSet={desktopSrc} />
          <img
            src={mobileSrc}
            alt="Wata Bautet"
            // Removed specific max-heights, let the container control it via h-full and object-contain
            className="h-full w-auto max-w-full object-contain object-bottom drop-shadow-[10px_10px_0px_rgba(0,0,0,1)]"
          />
        </picture>
      </div>
    </div>
  );
};