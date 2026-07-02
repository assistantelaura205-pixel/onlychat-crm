import { useEffect, useMemo, useRef, useState } from "react";
import { api } from "../api";

const euro = (n) => `${(n || 0).toFixed(0)}€`;
const initials = (s) => (s || "?").split(" ").map((w) => w[0]).join("").slice(0, 2).toUpperCase();
const time = (iso) => new Date(iso).toLocaleTimeString("fr-FR", { hour: "2-digit", minute: "2-digit" });

const FILTERS = [
  { key: "all", label: "Tous" },
  { key: "new", label: "Nouveaux" },
  { key: "unread", label: "Non lus" },
  { key: "to_reply", label: "À répondre" },
];

export default function Inbox() {
  const [agencyId, setAgencyId] = useState(null);
  const [accountId, setAccountId] = useState(null);
  const [accounts, setAccounts] = useState([]);
  const [tags, setTags] = useState([]);
  const [convs, setConvs] = useState([]);
  const [filter, setFilter] = useState("all");
  const [q, setQ] = useState("");
  const [active, setActive] = useState(null);
  const [messages, setMessages] = useState([]);
  const [draft, setDraft] = useState("");
  const [vaultOpen, setVaultOpen] = useState(false);
  const [vault, setVault] = useState([]);
  const msgEnd = useRef(null);

  // bootstrap
  useEffect(() => {
    api.agencies().then((ags) => {
      if (!ags[0]) return;
      setAgencyId(ags[0].id);
      api.accounts(ags[0].id).then((accs) => {
        setAccounts(accs);
        if (accs[0]) {
          setAccountId(accs[0].id);
          api.tags(ags[0].id, accs[0].id).then(setTags);
        }
      });
    });
  }, []);

  // load conversations
  useEffect(() => {
    if (agencyId && accountId) {
      api.conversations(agencyId, accountId, filter, q).then(setConvs);
    }
  }, [agencyId, accountId, filter, q]);

  // load messages when active changes
  useEffect(() => {
    if (agencyId && accountId && active) {
      api.messages(agencyId, accountId, active.id).then(setMessages);
    }
  }, [active]);

  useEffect(() => {
    msgEnd.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const tagMap = useMemo(() => Object.fromEntries(tags.map((t) => [t.id, t])), [tags]);

  async function send(mediaId = null) {
    if (!draft.trim() && !mediaId) return;
    const msg = await api.send(agencyId, accountId, active.id, { body: draft, media_id: mediaId });
    setMessages((m) => [...m, msg]);
    setDraft("");
    api.conversations(agencyId, accountId, filter, q).then(setConvs);
  }

  async function openVault() {
    const v = await api.vault(agencyId, accountId);
    setVault(v);
    setVaultOpen(true);
  }

  return (
    <div className="crm">
      {/* PANE 1 — Conversations */}
      <div className="conv-list">
        <div className="conv-search">
          <input placeholder="Rechercher un contact…" value={q} onChange={(e) => setQ(e.target.value)} />
        </div>
        <div className="filters">
          {FILTERS.map((f) => (
            <button
              key={f.key}
              className={"chip" + (filter === f.key ? " active" : "")}
              onClick={() => setFilter(f.key)}
            >
              {f.label}
            </button>
          ))}
        </div>
        <div className="conv-items">
          {convs.map((cv) => (
            <div
              key={cv.id}
              className={"conv-item" + (active?.id === cv.id ? " active" : "")}
              onClick={() => setActive(cv)}
            >
              <div className="avatar">{initials(cv.contact.display_name)}</div>
              <div className="meta">
                <div className="top">
                  <span className="name">{cv.contact.display_name}</span>
                  <span className="time">{time(cv.last_message_at)}</span>
                </div>
                <div className="preview">{cv.last_message_preview}</div>
                <div style={{ display: "flex", gap: 8, alignItems: "center", marginTop: 2 }}>
                  <span className="spent-badge">{euro(cv.contact.total_spent)}</span>
                  {cv.contact.tag_ids.map((id) =>
                    tagMap[id] ? (
                      <span key={id} className="tag" style={{ background: tagMap[id].color }}>
                        {tagMap[id].name}
                      </span>
                    ) : null
                  )}
                  {cv.pinned && <span className="pin">📌</span>}
                  {cv.unread_count > 0 && <span className="dot" />}
                </div>
              </div>
            </div>
          ))}
          {convs.length === 0 && <div style={{ padding: 20, color: "var(--muted)" }}>Aucune conversation</div>}
        </div>
      </div>

      {/* PANE 2 — Chat */}
      {active ? (
        <div className="chat">
          <div className="chat-header">
            <div className="avatar">{initials(active.contact.display_name)}</div>
            <div>
              <div className="name">{active.contact.display_name}</div>
              <div className="status">@{active.contact.username || "—"} · {active.contact.country}</div>
            </div>
          </div>
          <div className="messages">
            {messages.map((m) => (
              <div key={m.id} className={"bubble " + m.direction}>
                {m.body}
                {m.direction === "out" && m.sent_by_membership_id && (
                  <div className="attribution">envoyé par chatter</div>
                )}
              </div>
            ))}
            <div ref={msgEnd} />
          </div>
          <div className="composer">
            <button className="btn small secondary" onClick={openVault}>📎 Vault</button>
            <input
              placeholder="Écris ton message…"
              value={draft}
              onChange={(e) => setDraft(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && send()}
            />
            <button className="btn small" onClick={() => send()}>Envoyer</button>
          </div>
        </div>
      ) : (
        <div className="chat">
          <div className="empty">
            <div style={{ fontSize: 42 }}>💬</div>
            <div>Sélectionne une conversation</div>
          </div>
        </div>
      )}

      {/* PANE 3 — Contact */}
      {active ? (
        <ContactPane
          conv={active}
          tagMap={tagMap}
          onSave={(patch) =>
            api.updateContact(agencyId, accountId, active.contact.id, patch).then((c) =>
              setActive((a) => ({ ...a, contact: c }))
            )
          }
        />
      ) : (
        <div className="contact-pane" />
      )}

      {/* Vault modal */}
      {vaultOpen && (
        <div className="modal-overlay" onClick={() => setVaultOpen(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <h3 style={{ margin: 0 }}>Vault — envoyer un média</h3>
              <button className="link-btn" onClick={() => setVaultOpen(false)}>Fermer</button>
            </div>
            <p style={{ color: "var(--muted)", fontSize: 13 }}>
              Les médias avec un prix envoient le lien Dropfan (PPV). Les autres sont gratuits.
            </p>
            <div className="vault-grid">
              {vault.map((m) => (
                <div
                  key={m.id}
                  className="vault-item"
                  onClick={() => {
                    send(m.id);
                    setVaultOpen(false);
                  }}
                >
                  {m.price > 0 && <span className="price-tag">{euro(m.price)}</span>}
                  <div className="vault-thumb">{m.kind === "video" ? "🎬" : "🖼️"}</div>
                  <div className="cap">{m.filename}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function ContactPane({ conv, tagMap, onSave }) {
  const c = conv.contact;
  const [notes, setNotes] = useState(c.notes || "");
  const [spent, setSpent] = useState(c.total_spent || 0);

  useEffect(() => {
    setNotes(c.notes || "");
    setSpent(c.total_spent || 0);
  }, [c.id]);

  return (
    <div className="contact-pane">
      <div className="big-avatar">{initials(c.display_name)}</div>
      <h3>{c.display_name}</h3>
      <div className="uname">@{c.username || "—"}</div>

      <div className="section-label">Infos Telegram</div>
      <div className="info-row"><span className="k">Pays</span><span>{c.country || "—"}</span></div>
      <div className="info-row"><span className="k">Premium</span><span>{c.is_premium ? "Oui" : "Non"}</span></div>
      <div className="info-row"><span className="k">Métier</span><span>{c.occupation || "—"}</span></div>

      <div className="section-label">Tags</div>
      <div>
        {c.tag_ids.length === 0 && <span style={{ color: "var(--muted)", fontSize: 13 }}>Aucun</span>}
        {c.tag_ids.map((id) =>
          tagMap[id] ? (
            <span key={id} className="tag" style={{ background: tagMap[id].color }}>{tagMap[id].name}</span>
          ) : null
        )}
      </div>

      <div className="section-label">Financial insights</div>
      <div className="info-row">
        <span className="k">Total dépensé</span>
        <input
          style={{ width: 80, textAlign: "right", border: "1px solid var(--border)", borderRadius: 6, padding: "2px 6px" }}
          type="number"
          value={spent}
          onChange={(e) => setSpent(parseFloat(e.target.value) || 0)}
          onBlur={() => onSave({ total_spent: spent })}
        />
      </div>

      <div className="section-label">Notes</div>
      <textarea
        className="notes-area"
        value={notes}
        onChange={(e) => setNotes(e.target.value)}
        onBlur={() => onSave({ notes })}
        placeholder="Contexte, préférences, historique…"
      />
    </div>
  );
}
