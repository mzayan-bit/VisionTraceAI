import { useEffect, useRef } from 'react';
import { motion, useSpring, useTransform } from 'framer-motion';

function NumberColumn({ digit, delta }) {
  const spring = useSpring(0, { bounce: 0, duration: 800 });

  useEffect(() => {
    // When the target digit changes, animate the spring to the new target
    spring.set(digit);
  }, [digit, spring]);

  // Transform the spring value to a Y translation percentage
  const y = useTransform(spring, (value) => `-${value * 10}%`);

  return (
    <div style={{ position: 'relative', overflow: 'hidden', height: '1.2em', display: 'inline-block' }}>
      <motion.div style={{ y, display: 'flex', flexDirection: 'column' }}>
        {[0, 1, 2, 3, 4, 5, 6, 7, 8, 9].map((n) => (
          <span key={n} style={{ height: '1.2em', lineHeight: '1.2em' }}>
            {n}
          </span>
        ))}
      </motion.div>
    </div>
  );
}

export default function RollingNumber({ value }) {
  const valueStr = value.toString();
  const digits = valueStr.split('');

  return (
    <div style={{ display: 'inline-flex' }}>
      {digits.map((digit, i) => {
        // Just render normal character if not a number (e.g. commas)
        if (isNaN(parseInt(digit))) {
          return <span key={`${i}-${digit}`}>{digit}</span>;
        }
        return <NumberColumn key={i} digit={parseInt(digit)} />;
      })}
    </div>
  );
}
