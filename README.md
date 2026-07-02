# OnlyChat CRM (nom provisoire)

CRM Telegram pour agences OFM — inspiré de l'analyse Wysper (02/07/2026).
**Monétisation : liens Dropfan envoyés dans le chat** (pas de PSP intégré, pas de merchant of record).

## Stack
- **Backend** : FastAPI (Python 3.11+), SQLAlchemy 2.0, Telethon (MTProto), WebSocket temps réel
- **Frontend** : React + Vite
- **DB** : SQLite en local, PostgreSQL en prod (Railway) — même pattern qu'OnlyStats

## Démarrage local

### Backend
```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # renseigner TG_API_ID / TG_API_HASH (my.telegram.org)
python -m app.seed          # données démo (login: demo@onlychat.app / demo1234)
uvicorn app.main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev                 # http://localhost:5173 (proxy API → :8000)
```

## Architecture
```
frontend (React/Vite) ── REST + WebSocket ──> backend (FastAPI)
                                                │
                                    SQLite/PostgreSQL
                                                │
                                    Telethon clients (1 session par compte TG)
```

- **Connexion compte Telegram** : QR code (recommandé) — session MTProto user, invisible pour les fans, historique complet importé.
- **PPV via Dropfan** : chaque média du vault peut porter un `dropfan_url` + prix ; l'envoi poste le teaser + le lien dans Telegram. Le paiement se fait chez Dropfan ; on marque la vente manuellement (webhook plus tard si Dropfan en expose).
- **Multi-tenant** : agence → membres (owner/admin/manager/chatter) → comptes Telegram → conversations. Chaque message envoyé est attribué au membre qui l'a écrit.

## Roadmap (voir ANALYSE-WYSPER-CAHIER-DES-CHARGES.md)
- [x] Phase 1 : scaffold auth + agence + inbox + vault + dashboard
- [ ] Proxies par compte + warmup anti-ban
- [ ] Scheduled messages / automation pack
- [ ] Suggestions IA de réponses (différenciateur vs Wysper)
- [ ] App desktop Electron

## Prod (Railway)
Même pattern qu'OnlyStats : service frontend (Node) + service backend (Python) + Postgres.
`DATABASE_URL` bascule automatiquement SQLite → Postgres.
