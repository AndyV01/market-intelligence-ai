import Loader from "./Loader";

export default function Dashboard({ data, loading }) {
  if (loading) return <Loader />;

  if (!data) return <p>No hay datos aún</p>;

  return (
    <div>
      {/* 📄 Reporte */}
      <div style={{ marginBottom: 30 }}>
        <h2>📄 Reporte</h2>
        <pre style={{ whiteSpace: "pre-wrap" }}>
          {data.report}
        </pre>
      </div>

      {/* 🚀 Oportunidades */}
      <div>
        <h2>🚀 Oportunidades</h2>

        {data.opportunities?.map((op) => (
          <div
            key={op.asset}
            style={{
              border: "1px solid #333",
              padding: 16,
              marginBottom: 10,
              borderRadius: 8
            }}
          >
            <h3>
              {op.asset} — {op.signal}
            </h3>

            <p>Score: {op.final_score}</p>
            <p>Precio USD: ${op.price_usd}</p>
            <p>Asignación: ${op.suggested_amount_usd}</p>

            <ul>
              {op.key_signals?.map((s, i) => (
                <li key={i}>{s}</li>
              ))}
            </ul>
          </div>
        ))}
      </div>
    </div>
  );
}