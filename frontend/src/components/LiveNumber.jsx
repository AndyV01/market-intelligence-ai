import { useEffect, useState } from "react";

export default function LiveNumber({ value, duration = 800 }) {
  const [display, setDisplay] = useState(value || 0);

  useEffect(() => {
    let start = display;
    let end = value || 0;
    let startTime = null;

    function animate(ts) {
      if (!startTime) startTime = ts;
      const progress = Math.min((ts - startTime) / duration, 1);

      const current = start + (end - start) * progress;
      setDisplay(current);

      if (progress < 1) requestAnimationFrame(animate);
    }

    requestAnimationFrame(animate);
  }, [value]);

  return display.toFixed(2);
}