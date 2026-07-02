import { useEffect, useState } from "react";
import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { api, clearToken } from "../api";

export default function Shell() {
  const nav = useNavigate();
  const [me, setMe] = useState(null);

  useEffect(() => {
    api.me().then(setMe).catch(() => { clearToken(); nav("/login"); });
  }, []);

  function logout() {
    clearToken();
    nav("/login");
  }

  const initials = (me?.name || "?").slice(0, 2).toUpperCase();

  return (
    <div className="shell">
      <div className="sidebar">
        <div className="logo">⚡ OnlyChat</div>
        <div className="nav-label">Général</div>
        <NavLink to="/inbox" className={({ isActive }) => "nav-item" + (isActive ? " active" : "")}>
          💬 Inbox
        </NavLink>
        <NavLink to="/dashboard" className={({ isActive }) => "nav-item" + (isActive ? " active" : "")}>
          📊 Dashboard
        </NavLink>
        <div className="spacer" />
        <div className="user-chip">
          <div className="avatar">{initials}</div>
          <div style={{ flex: 1, minWidth: 0 }}>
            <div style={{ fontSize: 13, color: "#fff", fontWeight: 600 }}>{me?.name}</div>
            <button className="link-btn" style={{ color: "#94a3b8" }} onClick={logout}>
              Déconnexion
            </button>
          </div>
        </div>
      </div>
      <div className="main">
        <Outlet />
      </div>
    </div>
  );
}
