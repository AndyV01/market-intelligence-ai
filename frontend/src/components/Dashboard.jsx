import Loader from "./Loader";
import LiveNumber from "./LiveNumber";

export default function Dashboard({ data, loading }) {
  if (loading) return <Loader />;
  if (!data) return <p>No hay datos aún</p>;

  const argentina = data.argentina_instruments;

  function formatARS(n) {
    return `$${Number(n || 0).toLocaleString("es-AR")}`;
  }

  return (
    <div style={{ padding: 24, color: "#fff" }}>

      {/* 📄 Reporte */}
      <Section title="📄 Reporte">
        <p style={{ whiteSpace: "pre-wrap" }}>{data.report}</p>
      </Section>

      {/* 🇦🇷 Instrumentos */}
      {argentina && (
        <Section title="🇦🇷 Portfolio Argentina ($500.000 ARS)">
          <div style={grid}>

            {/* LECAP */}
            {argentina.LECAP?.map((i) => (
              <InstrumentCard
                key={i.symbol}
                title={i.symbol}
                type="LECAP"
                capital={i.capital}
                rate={i.tir || i.tir_anual}
                gain={i.gain_30d || i.ganancia_30d_ars}
                horizon={30}
              />
            ))}

            {/* CER */}
            {argentina.CER?.map((i) => (
              <InstrumentCard
                key={i.symbol}
                title={i.symbol}
                type="CER"
                capital={i.capital}
                rate={i.tir_real}
                gain={i.gain_30d || i.ganancia_30d_ars}
                horizon={30}
              />
            ))}

            {/* CAUCIÓN */}
            {argentina.CAUCION?.map((i) => (
              <InstrumentCard
                key={i.symbol || "caucion"}
                title="Caución bursátil"
                type="Money Market"
                capital={i.capital}
                rate={i.rate}
                gain={i.gain_30d}
                horizon={30}
              />
            ))}

          </div>
        </Section>
      )}

      {/* 🚀 Oportunidades */}
      <Section title="🚀 Oportunidades">
        <div style={grid}>

          {data.opportunities?.map((op) => (
            <div key={op.asset} style={card}>

              <h3>{op.asset}</h3>

              <span style={signalTag(op.signal)}>
                {op.signal}
              </span>

              <p>Score: {op.final_score}</p>
              <p>Precio: ${op.price_usd}</p>
              <p>Asignación: ${op.suggested_amount_usd}</p>

              <ul style={{ paddingLeft: 16 }}>
                {op.key_signals?.map((s, i) => (
                  <li key={i}>{s}</li>
                ))}
              </ul>

            </div>
          ))}

        </div>
      </Section>

    </div>
  );
}

//////////////////////////////////////////////////
// COMPONENTE CARD (ÚNICO Y CORRECTO)
//////////////////////////////////////////////////

function InstrumentCard({ title, type, capital, rate, gain, horizon }) {
  const isBad = (gain || 0) <= 0;
  const finalValue = (capital || 0) + (gain || 0);

  return (
    <div style={{
      padding: 14,
      borderRadius: 12,
      background: "rgba(10, 14, 25, 0.65)",
      backdropFilter: "blur(12px)",
      border: `1px solid ${isBad ? "rgba(255,80,80,0.25)" : "rgba(0,255,150,0.25)"}`,
      boxShadow: isBad
        ? "0 0 20px rgba(255,80,80,0.08)"
        : "0 0 20px rgba(0,255,150,0.08)",
      fontSize: 13,
      transition: "0.2s ease",
    }}>

      <div style={{ display: "flex", justifyContent: "space-between" }}>
        <strong style={{ fontSize: 16 }}>{title}</strong>
        <span style={{ opacity: 0.6 }}>{type}</span>
      </div>

      <p>Capital: ${Number(capital || 0).toFixed(2)}</p>
      <p>Tasa anual: {((rate || 0) * 100).toFixed(1)}%</p>
      <p>Horizonte: {horizon} días</p>

      <p style={{
        color: isBad ? "#ff5252" : "#00e676",
        fontWeight: "bold"
      }}>
        Ganancia 30d: $<LiveNumber value={gain} />
      </p>

      <p>Final: $<LiveNumber value={finalValue} /></p>

      {isBad && (
        <p style={{ color: "#ff5252", fontSize: 12 }}>
          ⚠ No conviene invertir ahora
        </p>
      )}
    </div>
  );
}

//////////////////////////////////////////////////
// UI
//////////////////////////////////////////////////

function Section({ title, children }) {
  return (
    <div style={{ marginBottom: 40 }}>
      <h2 style={{ marginBottom: 16 }}>{title}</h2>
      {children}
    </div>
  );
}

const grid = {
  display: "grid",
  gridTemplateColumns: "repeat(auto-fill, minmax(220px, 1fr))",
  gap: 16,
};

const card = {
  backdropFilter: "blur(12px)",
  background: "rgba(255,255,255,0.05)",
  border: "1px solid rgba(255,255,255,0.1)",
  borderRadius: 18,
  padding: 20,
  boxShadow: "0 10px 40px rgba(0,0,0,0.3)",
};

const signalTag = (signal) => ({
  fontSize: 12,
  padding: "4px 10px",
  borderRadius: 10,
  marginBottom: 10,
  display: "inline-block",
  background:
    signal === "STRONG_BUY"
      ? "#00e676"
      : signal === "BUY"
      ? "#69f0ae"
      : signal === "SELL"
      ? "#ff5252"
      : "rgba(255,255,255,0.1)",
  color: "#000",
});