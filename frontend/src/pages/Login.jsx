import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { api, setToken } from "../api";

export default function Login() {
  const nav = useNavigate();
  const [mode, setMode] = useState("login");
  const [email, setEmail] = useState("demo@onlychat.app");
  const [password, setPassword] = useState("demo1234");
  const [name, setName] = useState("");
  const [agency, setAgency] = useState("");
  const [err, setErr] = useState("");
  const [loading, setLoading] = useState(false);

  async function submit(e) {
    e.preventDefault();
    setErr("");
    setLoading(true);
    try {
      const res =
        mode === "login"
          ? await api.login(email, password)
          : await api.register({ email, name, password, agency_name: agency });
      setToken(res.access_token);
      nav("/inbox");
    } catch (e) {
      setErr(e.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="auth-wrap">
      <form className="auth-card" onSubmit={submit}>
        <h1>OnlyChat CRM</h1>
        <p className="sub">{mode === "login" ? "Connecte-toi à ton espace" : "Crée ton agence"}</p>

        {mode === "register" && (
          <>
            <div className="field">
              <label>Ton nom</label>
              <input value={name} onChange={(e) => setName(e.target.value)} required />
            </div>
            <div className="field">
              <label>Nom de l'agence</label>
              <input value={agency} onChange={(e) => setAgency(e.target.value)} required />
            </div>
          </>
        )}
        <div className="field">
          <label>Email</label>
          <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
        </div>
        <div className="field">
          <label>Mot de passe</label>
          <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} required />
        </div>

        {err && <div className="error">{err}</div>}

        <button className="btn" disabled={loading}>
          {loading ? "..." : mode === "login" ? "Se connecter" : "Créer mon agence"}
        </button>

        <div style={{ marginTop: 16, textAlign: "center" }}>
          <button
            type="button"
            className="link-btn"
            onClick={() => setMode(mode === "login" ? "register" : "login")}
          >
            {mode === "login" ? "Créer une agence" : "J'ai déjà un compte"}
          </button>
        </div>
      </form>
    </div>
  );
}
