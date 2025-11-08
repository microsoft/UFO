import React, { useMemo } from 'react';

interface StarConfig {
  id: string;
  left: number;
  top: number;
  size: number;
  delay: number;
  duration: number;
  twinkle: boolean;
}

interface ShootingStarConfig {
  id: string;
  delay: number;
  top: number;
  start: number;
}

const buildStars = (count: number): StarConfig[] =>
  Array.from({ length: count }, (_, index) => ({
    id: `star-${index}`,
    left: Math.random() * 100,
    top: Math.random() * 100,
    size: Math.random() * 0.7 + 0.35,
    delay: Math.random() * 10,
    duration: Math.random() * 12 + 10,
    twinkle: Math.random() > 0.55,
  }));

const buildShootingStars = (count: number): ShootingStarConfig[] =>
  Array.from({ length: count }, (_, index) => ({
    id: `shooting-${index}`,
    delay: Math.random() * 45 + index * 30,
    top: Math.random() * 60 + 10,
    start: Math.random() * 50,
  }));

const StarfieldOverlay: React.FC = () => {
  const stars = useMemo(() => buildStars(14), []);
  const shootingStars = useMemo(() => buildShootingStars(1), []);

  return (
    <div className="absolute inset-0 overflow-hidden">
      {stars.map((star) => (
        <span
          key={star.id}
          className={`star-particle${star.twinkle ? ' star-twinkle' : ''}`}
          style={{
            left: `${star.left}%`,
            top: `${star.top}%`,
            width: `${star.size}rem`,
            height: `${star.size}rem`,
            animationDelay: `${star.delay}s`,
            animationDuration: `${star.duration}s`,
          }}
          aria-hidden
        />
      ))}
      {shootingStars.map((trail) => (
        <span
          key={trail.id}
          className="shooting-star"
          style={{
            top: `${trail.top}%`,
            left: `${trail.start}%`,
            animationDelay: `${trail.delay}s`,
          }}
          aria-hidden
        />
      ))}
    </div>
  );
};

export default StarfieldOverlay;
