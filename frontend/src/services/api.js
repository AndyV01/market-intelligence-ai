const API_URL = "http://localhost:8000/api/v1";

export async function runAnalysisSync() {
  const res = await fetch(`${API_URL}/analyze/sync`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({
      assets: ["BTC", "ETH", "SOL"],
      budget_ars: 500000
    })
  });

  if (!res.ok) {
    throw new Error("Error en API");
  }

  return res.json();
}