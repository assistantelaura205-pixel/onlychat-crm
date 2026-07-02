# Déployer OnlyChat CRM sur Railway

Même structure qu'OnlyStats : **3 services dans un même projet Railway** → 1 backend, 1 frontend, 1 Postgres.

---

## Étape 0 — Pousser le code sur GitHub
Railway déploie depuis un repo Git. Crée un repo (ex. `onlychat-crm`) et pousse le dossier.
```bash
cd onlychat-crm
git init && git add . && git commit -m "init OnlyChat CRM"
git remote add origin git@github.com:TON-COMPTE/onlychat-crm.git
git push -u origin main
```

## Étape 1 — Créer le projet + Postgres
1. Railway → **New Project** → **Deploy PostgreSQL**. Ça crée la base et une variable `DATABASE_URL`.

## Étape 2 — Service backend
1. Dans le projet → **New** → **GitHub Repo** → choisis `onlychat-crm`.
2. **Settings → Root Directory** = `backend`.
3. **Variables** (onglet Variables) :
   - `DATABASE_URL` = référence la base : clique "Add Reference" → Postgres → `DATABASE_URL` (Railway remplit tout seul).
   - `SECRET_KEY` = une longue chaîne random (ex. `openssl rand -hex 32`).
   - `TG_API_ID` et `TG_API_HASH` = tes identifiants depuis https://my.telegram.org/apps (laisse vides au début = mode démo).
4. Railway build tout seul (Nixpacks détecte Python + `requirements.txt`) et lance la commande du `railway.json`.
5. **Settings → Networking → Generate Domain** → tu obtiens l'URL publique du backend, ex. `https://onlychat-backend-production.up.railway.app`. **Note-la.**

## Étape 3 — Service frontend
1. Dans le projet → **New** → **GitHub Repo** → même repo `onlychat-crm`.
2. **Settings → Root Directory** = `frontend`.
3. **Variables** :
   - `VITE_API_BASE` = l'URL du backend notée à l'étape 2 (ex. `https://onlychat-backend-production.up.railway.app`).
     ⚠️ Cette variable est lue **au build** → si tu la changes, il faut redéployer le frontend.
4. Railway lance `npm install` → `npm run build` → `npm run start` (vite preview sur `$PORT`).
5. **Generate Domain** → c'est **ton URL finale**, celle que tu ouvres et partages, ex. `https://onlychat-production.up.railway.app`.

## Étape 4 — Initialiser la base (une fois)
Les tables se créent automatiquement au 1er démarrage du backend. Pour charger les données démo :
- soit tu enlèves le seed en prod (recommandé : crée ton vrai compte via l'écran d'inscription),
- soit, pour tester, ouvre un shell Railway sur le backend et lance `python -m app.seed` (⚠️ ça **efface** et re-remplit la base).

---

## Récap des variables

| Service | Variable | Valeur |
|---|---|---|
| Backend | `DATABASE_URL` | référence Postgres (auto) |
| Backend | `SECRET_KEY` | random 32+ chars |
| Backend | `TG_API_ID` / `TG_API_HASH` | my.telegram.org (optionnel au début) |
| Frontend | `VITE_API_BASE` | URL publique du backend |

## Notes
- **CORS** est déjà ouvert (`*`) côté backend — tu peux le restreindre à ton domaine frontend plus tard (`app/main.py`).
- **WebSocket temps réel** : fonctionne sur le même domaine backend (Railway supporte le WS nativement).
- **Coût** : 3 petits services ≈ le même ordre de grandeur qu'OnlyStats. Postgres inclus.
- **Sécurité** : mets un vrai `SECRET_KEY` et ne commit jamais ton `.env` (déjà dans `.gitignore`).
