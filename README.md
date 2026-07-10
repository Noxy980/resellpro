# ResellPro

Assistant professionnel d'achat-revente Vinted avec IA intégrée (OpenRouter).

## Déploiement web (Netlify)

**Guide complet : [DEPLOY-NETLIFY.md](./DEPLOY-NETLIFY.md)**

Résumé en 3 étapes :
1. Déployer l'API sur **Render** (gratuit) avec `render.yaml`
2. Déployer le site sur **Netlify** — le fichier `netlify.toml` configure tout automatiquement
3. Ajouter `VITE_API_URL=https://votre-api.onrender.com/api` dans les variables Netlify

## Fonctionnalités

- **Dashboard** — opportunités, bénéfices, stock, conseils IA saisonniers
- **Bot intelligent** — recherche adaptée à la saison, score /100
- **Assistant IA** — chat, analyse, génération d'annonces (OpenRouter gratuit)
- **Mon Vinted** — connexion, annonces, ventes, favoris
- **Stock** — CRUD complet, statuts, marge, ROI
- **AI Photo Studio** — amélioration photos produit

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

→ http://localhost:5173

## Architecture

```
vinted-resale-assistant/
├── desktop/          # Site React (Netlify)
├── backend/          # API FastAPI (Render)
├── src/              # Moteur d'analyse Python
├── netlify.toml      # Config Netlify
├── render.yaml       # Config Render
└── DEPLOY-NETLIFY.md # Guide de déploiement
```

## Variables d'environnement

Copiez `.env.example` vers `.env` pour le développement local.

Sur **Netlify** : `VITE_API_URL`  
Sur **Render** : `OPENROUTER_API_KEY`, `ALLOWED_ORIGINS`

## Desktop / Mobile (optionnel)

L'app Electron et Capacitor restent disponibles dans `desktop/` :

```powershell
cd desktop
npm run start      # Electron
npm run cap:sync   # Mobile
```
