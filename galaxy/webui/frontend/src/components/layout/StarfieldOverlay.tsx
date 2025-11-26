import React, { useMemo } from 'react';

interface StarConfig {
  id: string;
  left: number;
  top: number;
  size: number;
  opacity: number;
  color: 'white' | 'blue' | 'yellow' | 'orange' | 'red';
}

interface ShootingStarConfig {
  id: string;
  top: number;
  left: number;
  width: number;
  opacity: number;
}

const buildStars = (count: number): StarConfig[] => {
  const colors: Array<'white' | 'blue' | 'yellow' | 'orange' | 'red'> = ['white', 'blue', 'yellow', 'orange', 'red'];
  // Weight distribution: more white/blue stars (common), fewer red/orange (rare)
  const colorWeights = [0.35, 0.30, 0.20, 0.10, 0.05];
  
  return Array.from({ length: count }, (_, index) => {
    // Pick random color based on weights
    const rand = Math.random();
    let cumulative = 0;
    let selectedColor: 'white' | 'blue' | 'yellow' | 'orange' | 'red' = 'white';
    
    for (let i = 0; i < colors.length; i++) {
      cumulative += colorWeights[i];
      if (rand < cumulative) {
        selectedColor = colors[i];
        break;
      }
    }
    
    return {
      id: `star-${index}`,
      left: Math.random() * 100,
      top: Math.random() * 100,
      size: Math.random() * 0.5 + 0.25,
      opacity: Math.random() * 0.4 + 0.2,
      color: selectedColor,
    };
  });
};

const buildShootingStars = (count: number): ShootingStarConfig[] =>
  Array.from({ length: count }, (_, index) => ({
    id: `shooting-${index}`,
    top: Math.random() * 60 + 10,
    left: Math.random() * 80,
    width: Math.random() * 100 + 120,
    opacity: Math.random() * 0.3 + 0.3,
  }));

const StarfieldOverlay: React.FC = () => {
  // Static stars avoid continuous animations while keeping the background rich
  const stars = useMemo(() => buildStars(40), []);
  const shootingStars = useMemo(() => buildShootingStars(3), []);

  return (
    <div className="absolute inset-0 overflow-hidden pointer-events-none">
      {stars.map((star) => (
        <span
          key={star.id}
          className="star-static"
          data-color={star.color}
          style={{
            left: `${star.left}%`,
            top: `${star.top}%`,
            width: `${star.size}rem`,
            height: `${star.size}rem`,
            opacity: star.opacity,
          }}
          aria-hidden
        />
      ))}
      {shootingStars.map((trail) => (
        <span
          key={trail.id}
          className="shooting-star-static"
          style={{
            top: `${trail.top}%`,
            left: `${trail.left}%`,
            width: `${trail.width}px`,
            opacity: trail.opacity,
          }}
          aria-hidden
        />
      ))}
    </div>
  );
};

export default StarfieldOverlay;
