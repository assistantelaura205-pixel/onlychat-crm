import { useEffect, useState } from "react";
import { api } from "../api";

const euro = (n) => `${(n || 0).toFixed(2)} €`;

export default function Dashboard() {
  const [data, setData] = useState(null);
  const [agencyId, setAgencyId] = useState(null);

  useEffect(() => {
    api.agencies().then((ags) => {
      if (ags[0]) {
        setAgencyId(ags[0].id);
        api.dashboard(ags[0].id).then(setData);
      }
    });
  }, []);

  if (!data) return <div className="page">Chargement…</div>;

  const kpis = [
    { label: "Total des gains", value: euro(data.total_earnings) },
    { label: "PPV", value: euro(data.ppv_earnings) },
    { label: "Nouvelles conversations", value: data.new_conversations },
    { label: "Taux de réponse", value: `${data.response_rate}%` },
  ];

  return (
    <div className="page">
      <h1>Dashboard</h1>
      <div className="kpi-grid">
        {kpis.map((k) => (
          <div className="kpi" key={k.label}>
            <div className="label">{k.label}</div>
            <div className="value">{k.value}</div>
          </div>
        ))}
      </div>

      <div className="card">
        <h3 style={{ marginTop: 0 }}>Performance par membre</h3>
        <table>
          <thead>
            <tr>
              <th>Membre</th>
              <th>Rôle</th>
              <th style={{ textAlign: "right" }}>Revenus</th>
            </tr>
          </thead>
          <tbody>
            {data.per_member.map((m) => (
              <tr key={m.email}>
                <td>
                  <strong>{m.name}</strong>
                  <div style={{ color: "var(--muted)", fontSize: 12 }}>{m.email}</div>
                </td>
                <td>{m.role}</td>
                <td style={{ textAlign: "right", color: "var(--green)", fontWeight: 700 }}>{euro(m.revenue)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
