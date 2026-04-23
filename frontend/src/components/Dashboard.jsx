import Loader from "./Loader";

export default function Dashboard({ data, loading }) {
  if (loading) return <Loader />;
  if (!data) return <p>No hay datos aún</p>;

  const macro = data.macro_allocation;
  const argentina = data.argentina_instruments;
  const budget = data.budget_usd || 300;

  return (
    <div style={{ padding: 24, color: "#fff" }}>

      {/* 📄 Reporte */}
      <Section title="📄 Reporte">
        <p style={{ whiteSpace: "pre-wrap" }}>{data.report}</p>
      </Section>

      {/* 🇦🇷 Instrumentos */}
      {argentina && (
        <Section title="🇦🇷 Instrumentos">
          <div style={grid}>

            {/* LECAP */}
            {argentina.LECAP?.map((i) => {
              const alloc = (macro?.LECAP || 0) * budget;

              const gain = i.rendimiento_30d
                ? alloc * i.rendimiento_30d
                : 0;

              return (
                <InstrumentCard
                  key={i.symbol}
                  title={`${i.symbol}`}
                  type="LECAP"
                  capital={alloc}
                  rate={i.tir_anual}
                  gain={gain}
                  horizon={i.horizon_days}
                />
              );
            })}

            {/* CER */}
            {argentina.CER?.map((i) => {
              const alloc = (macro?.CER || 0) * budget;

              // asumimos TIR anual → lo bajamos a 30 días
              const rate30d = (i.tir_real / 365) * 30;
              const gain = alloc * rate30d;

              return (
                <InstrumentCard
                  key={i.symbol}
                  title={`${i.symbol}`}
                  type="CER"
                  capital={alloc}
                  rate={i.tir_real}
                  gain={gain}
                  horizon={30}
                />
              );
            })}

            {/* USD (proxy carry 0% → solo informativo) */}
            {argentina.USD && (
              <div style={card}>
                <h3>Dólar</h3>
                <span style={tag}>FX</span>

                <p>MEP: ${argentina.USD.mep}</p>
                <p>CCL: ${argentina.USD.ccl}</p>
                <p>Blue: ${argentina.USD.blue}</p>

                <p style={{ opacity: 0.6 }}>
                  Sin rendimiento directo (reserva de valor)
                </p>
              </div>
            )}

          </div>
        </Section>
      )}

      {/* 🚀 Oportunidades (MEJORADAS, NO BORRADAS) */}
      <Section title="🚀 Oportunidades">
        <div style={grid}>

          {data.opportunities?.map((op) => (
            <div key={op.asset} style={card}>

              <h3>
                {op.asset}
              </h3>

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

/* ========================= */
/* COMPONENTE REUTILIZABLE */
/* ========================= */

function InstrumentCard({ title, type, capital, rate, gain, horizon }) {
  const isBad = gain <= 0;
  const finalValue = capital + gain;

  return (
    <div style={card}>
      <h3>{title}</h3>
      <span style={tag}>{type}</span>

      <p>Capital: ${capital.toFixed(2)}</p>
      <p>Tasa anual: {(rate * 100).toFixed(1)}%</p>
      <p>Horizonte: {horizon} días</p>

      <p style={{ color: isBad ? "#ff5252" : "#00e676", fontWeight: "bold" }}>
        Ganancia: ${gain.toFixed(2)}
      </p>

      <p>Final: ${finalValue.toFixed(2)}</p>

      {isBad && (
        <p style={warning}>
          ⚠️ No conviene invertir ahora
        </p>
      )}
    </div>
  );
}

/* ========================= */
/* UI */
/* ========================= */

function Section({ title, children }) {
  return (
    <div style={{ marginBottom: 40 }}>
      <h2 style={{ marginBottom: 16 }}>{title}</h2>
      {children}
    </div>
  );
}

const grid = {
  display: "flex",
  flexWrap: "wrap",
  gap: 20,
};

const card = {
  backdropFilter: "blur(12px)",
  background: "rgba(255,255,255,0.05)",
  border: "1px solid rgba(255,255,255,0.1)",
  borderRadius: 18,
  padding: 20,
  width: 260,
  boxShadow: "0 10px 40px rgba(0,0,0,0.3)",
  transition: "0.2s",
};

const tag = {
  fontSize: 12,
  padding: "4px 10px",
  background: "rgba(255,255,255,0.1)",
  borderRadius: 10,
  display: "inline-block",
  marginBottom: 10,
};

const warning = {
  color: "#ff5252",
  fontWeight: "bold",
  marginTop: 10,
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