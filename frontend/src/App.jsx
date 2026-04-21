import { useEffect, useState } from "react";
import Dashboard from "./components/Dashboard";
import { runAnalysisSync } from "./services/api";

export default function App() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);

  const runAnalysis = async () => {
    try {
      setLoading(true);
      const res = await runAnalysisSync();
      setData(res);
    } catch (err) {
      console.error("Error:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    runAnalysis();

    const interval = setInterval(runAnalysis, 120000); 

    return () => clearInterval(interval);
  }, []);

  return (
    <div style={{ padding: 20 }}>
      <h1>📊 Market Intelligence</h1>

      <Dashboard data={data} loading={loading} />
    </div>
  );
}