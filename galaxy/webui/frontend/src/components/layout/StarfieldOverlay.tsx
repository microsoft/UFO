import React, { useMemo } from 'react';

interface StarConfig {
  id: string;
  left: number;
  top: number;
  size: number;
  opacity: number;
}

interface ShootingStarConfig {
  id: string;
  top: number;
  left: number;
  width: number;
  opacity: number;
}

const buildStars = (count: number): StarConfig[] =>
  Array.from({ length: count }, (_, index) => ({
    id: `star-${index}`,
    left: Math.random() * 100,
    top: Math.random() * 100,
    size: Math.random() * 0.5 + 0.25,
    opacity: Math.random() * 0.4 + 0.2,
  }));

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
