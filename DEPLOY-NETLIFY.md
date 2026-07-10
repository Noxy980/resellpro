# Déployer ResellPro sur Netlify

ResellPro est composé de **deux parties** :

| Composant | Hébergement | Rôle |
|-----------|-------------|------|
| **Site web** (interface) | **Netlify** | React — gratuit, rapide |
| **API backend** (Python) | **Render** (gratuit) | FastAPI, IA, Vinted, stock |

Netlify héberge uniquement le site statique. L'API Python doit tourner sur un serveur séparé (Render recommandé).

---

## Étape 1 — Déployer l'API sur Render (gratuit)

1. Créez un compte sur [render.com](https://render.com)
2. **New → Blueprint** et connectez votre repo GitHub
3. Render détecte `render.yaml` et crée le service `resellpro-api`
4. Dans les variables d'environnement Render, ajoutez :
   - `OPENROUTER_API_KEY` = votre clé OpenRouter
   - `ALLOWED_ORIGINS` = `https://votre-site.netlify.app` (à mettre à jour après l'étape 2)
5. Attendez le déploiement → notez l'URL, ex. `https://resellpro-api.onrender.com`

Test : ouvrez `https://resellpro-api.onrender.com/api/monitor/status` — vous devez voir du JSON.

> Le plan gratuit Render met le serveur en veille après 15 min d'inactivité. Le premier appel peut prendre ~30 secondes.

---

## Étape 2 — Déployer le site sur Netlify

### Option A — Depuis GitHub (recommandé)

1. Poussez le projet sur GitHub
2. [app.netlify.com](https://app.netlify.com) → **Add new site → Import an existing project**
3. Choisissez le repo
4. Netlify lit automatiquement `netlify.toml` :
   - **Base directory** : `desktop` (défini dans netlify.toml)
   - **Build command** : `npm ci && npm run build`
   - **Publish directory** : `dist`
5. **Variables d'environnement** (Site settings → Environment variables) :

   | Variable | Valeur |
   |----------|--------|
   | `VITE_API_URL` | `https://resellpro-api.onrender.com/api` |

6. **Deploy site**

### Option B — Drag & drop

```powershell
cd desktop
npm install
$env:VITE_API_URL="https://resellpro-api.onrender.com/api"
npm run build
```

Glissez le dossier `desktop/dist` sur [app.netlify.com/drop](https://app.netlify.com/drop).

---

## Étape 3 — Finaliser CORS

Retournez sur Render et mettez à jour :

```
ALLOWED_ORIGINS=https://votre-nom.netlify.app
```

Redéployez le service Render.

---

## Développement local

```powershell
# Terminal 1 — API
cd backend
pip install -r requirements.txt
python run.py

# Terminal 2 — Site
cd desktop
npm install
npm run dev
```

→ http://localhost:5173 (l'API locale est utilisée automatiquement)

---

## Variables d'environnement

### Netlify (build time)

| Variable | Description |
|----------|-------------|
| `VITE_API_URL` | URL complète de l'API avec `/api` à la fin |

### Render (runtime)

| Variable | Description |
|----------|-------------|
| `OPENROUTER_API_KEY` | Clé OpenRouter pour l'IA |
| `ALLOWED_ORIGINS` | URL Netlify autorisée (CORS) |
| `PORT` | Défini automatiquement par Render |

---

## Dépannage

**Page blanche ou erreurs réseau**
→ Vérifiez `VITE_API_URL` dans Netlify et redéployez (la variable est injectée au *build*, pas au runtime).

**« API non configurée »**
→ `VITE_API_URL` manquante dans Netlify → Site settings → Environment variables → Trigger deploy.

**Backend lent au premier chargement**
→ Normal sur Render gratuit (cold start). Réessayez après 30 secondes.

**Connexion Vinted**
→ Fonctionne via l'API backend. La session est stockée côté serveur Render.

---

## Structure Netlify

```
netlify.toml          ← configuration automatique
desktop/
  dist/               ← dossier publié après build
  src/                ← code React
backend/              ← déployé séparément sur Render
render.yaml           ← configuration Render
```
