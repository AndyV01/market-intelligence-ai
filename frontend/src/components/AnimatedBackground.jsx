import { useEffect } from "react";

export default function AnimatedBackground() {

  // ✅ inyecta animaciones correctamente
  useEffect(() => {
    const style = document.createElement("style");

    style.innerHTML = `
      @keyframes moveLine {
        0% { transform: translateX(0); }
        100% { transform: translateX(-200px); }
      }

      @keyframes moveLineReverse {
        0% { transform: translateX(0); }
        100% { transform: translateX(200px); }
      }
    `;

    document.head.appendChild(style);

    return () => {
      document.head.removeChild(style);
    };
  }, []);

  return (
    <div style={bgContainer}>
      <div style={gradient}></div>
      <div style={grid}></div>

      <svg style={lines} viewBox="0 0 1440 600">
        <path
          d="M0,300 Q200,200 400,300 T800,300 T1200,250 T1440,300"
          style={lineGreen}
        />
        <path
          d="M0,350 Q200,450 400,350 T800,350 T1200,400 T1440,350"
          style={lineRed}
        />
      </svg>

      <div style={glow}></div>
    </div>
  );
}

/* ========================= */
/* STYLES */
/* ========================= */

const bgContainer = {
  position: "fixed",
  top: 0,
  left: 0,
  width: "100%",
  height: "100%",
  zIndex: -1,
  overflow: "hidden",
  background: "#05070d",
};

const gradient = {
  position: "absolute",
  width: "100%",
  height: "100%",
  background:
    "radial-gradient(circle at 20% 30%, rgba(0,255,150,0.08), transparent 40%), radial-gradient(circle at 80% 70%, rgba(255,0,100,0.08), transparent 40%)",
};

const grid = {
  position: "absolute",
  width: "100%",
  height: "100%",
  backgroundImage:
    "linear-gradient(rgba(255,255,255,0.03) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.03) 1px, transparent 1px)",
  backgroundSize: "40px 40px",
};

const lines = {
  position: "absolute",
  width: "100%",
  height: "100%",
  opacity: 0.4,
};

const lineGreen = {
  fill: "none",
  stroke: "#00e676",
  strokeWidth: 2,
  animation: "moveLine 8s linear infinite",
};

const lineRed = {
  fill: "none",
  stroke: "#ff5252",
  strokeWidth: 2,
  animation: "moveLineReverse 10s linear infinite",
};

const glow = {
  position: "absolute",
  width: "100%",
  height: "100%",
  boxShadow: "inset 0 0 200px rgba(0,0,0,0.9)",
};
