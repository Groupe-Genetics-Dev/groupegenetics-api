# API Groupe Genetics - Gestion des Incidents

<div align="center">
  <h3>🚀 API FastAPI pour la gestion des incidents et support technique</h3>
  <p>Solution complète de ticketing et de suivi des incidents pour le Groupe Genetics</p>
</div>

---

## ⚡ Démarrage rapide

### 🐳 Avec Docker (recommandé)

Prérequis : Docker + Docker Compose v2.

```bash
cp .env.example .env          # puis renseigner SECRET_KEY et SMTP_PASSWORD
docker compose up -d --build  # lance PostgreSQL + l'API
docker compose logs -f api    # suivre les logs
```

- Les migrations Alembic (`alembic upgrade head`) sont appliquées automatiquement au démarrage du conteneur.
- API : http://localhost:8000 — Swagger : http://localhost:8000/docs
- Les données PostgreSQL (`postgres_data`) et les rapports PDF (`reports_data`) sont conservés dans des volumes Docker.
- Arrêter : `docker compose down` (ajouter `-v` pour supprimer aussi les données).

### 💻 En local (sans Docker)

Prérequis : Python 3.11, PostgreSQL 12+.

```bash
python -m venv venv && source venv/bin/activate   # Windows : venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env    # remplacer "@db:" par "@localhost:" dans POSTGRES_URL
createdb genetics_incidents
alembic upgrade head
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## 📋 Table des Matières

- [À Propos](#-à-propos)
- [Fonctionnalités](#-fonctionnalités)
- [Technologies](#-technologies)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Utilisation](#-utilisation)
- [Documentation API](#-documentation-api)
- [Architecture](#-architecture)
- [Sécurité](#-sécurité)
- [Déploiement](#-déploiement)
- [Contribution](#-contribution)

## 🎯 À Propos

Cette API FastAPI permet au **Groupe Genetics** de gérer efficacement les incidents techniques et les demandes de support de ses clients. Elle offre un système complet de ticketing avec authentification, notifications par email, génération de rapports PDF et tableau de bord pour les dirigeants.

### 🎭 Rôles Utilisateurs

- **👤 Utilisateurs Standard** : Création et suivi de leurs incidents
- **👑 CEO/Administrateurs** : Vue globale, gestion des statuts, rapports détaillés
- **📧 Support** : Notifications automatiques pour tous les nouveaux incidents

## ✨ Fonctionnalités

### 🔐 **Authentification & Sécurité**
- Authentification JWT avec tokens sécurisés
- Système de réinitialisation de mot de passe par OTP
- Protection des routes sensibles
- Gestion des permissions par rôle

### 🎫 **Gestion des Incidents**
- ✅ Création, modification, suppression d'incidents
- 🏷️ Catégorisation (Réseau, Sécurité, Logiciel, Matériel, etc.)
- ⚡ Niveaux de priorité (Faible, Moyenne, Haute, Critique)
- 📊 Suivi des statuts (En attente, En traitement, Terminé)
- 🔍 Recherche et filtrage avancés

### 📧 **Notifications Automatiques**
- Alerte instantanée au support lors de nouveaux incidents
- Confirmation de résolution aux utilisateurs
- OTP par email pour réinitialisation de mot de passe
- Messages de contact dirigés vers l'équipe

### 📈 **Rapports & Analytics**
- 📊 Génération de rapports PDF détaillés
- 📉 Graphiques de répartition des incidents
- 👥 Top des utilisateurs les plus actifs
- 📅 Filtrage par période personnalisée
- 💾 Stockage et téléchargement des rapports

### 📞 **Contact & Support**
- Formulaire de contact intégré
- Routage automatique vers l'équipe support
- Traçabilité des demandes

## 🛠️ Technologies

### **Backend**
- **FastAPI** 0.104+ - Framework web moderne et performant
- **SQLAlchemy** 2.0+ - ORM pour base de données
- **Pydantic** 2.0+ - Validation des données
- **PostgreSQL** - Base de données relationnelle
- **Alembic** - Migrations de base de données

### **Sécurité**
- **python-jose** - Gestion des tokens JWT
- **passlib** avec bcrypt - Hachage des mots de passe
- **python-multipart** - Gestion des formulaires

### **Notifications**
- **httpx** - Client HTTP asynchrone
- **SMTP** (smtplib) - Envoi des emails via la boîte support

### **Rapports & Analytics**
- **ReportLab** - Génération de PDF
- **Pandas** - Analyse de données
- **Matplotlib** - Graphiques et visualisations

### **Développement**
- **python-dotenv** - Gestion des variables d'environnement
- **Rich** - Logging et console colorée
- **UUID** - Identifiants uniques

## 🚀 Installation

### Prérequis
- Python 3.9+
- PostgreSQL 12+
- Une boîte e-mail avec accès SMTP (ex. Hostinger) pour les emails

### 1. Cloner le Repository
```bash
git clone https://github.com/groupe-genetics/api-incidents.git
cd api-incidents
```

### 2. Environnement Virtuel
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate     # Windows
```

### 3. Installer les Dépendances
```bash
pip install -r requirements.txt
```

### 4. Configuration Base de Données
```bash
# Créer la base de données PostgreSQL
createdb genetics_incidents

# Appliquer les migrations
alembic upgrade head
```

## ⚙️ Configuration

### Variables d'Environnement

Créez un fichier `.env` à la racine :

```env
# 🔗 Base de données
POSTGRES_URL=postgresql://username:password@localhost:5432/genetics_incidents

# 🔐 Sécurité JWT
SECRET_KEY=your-super-secret-key-here-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# 🌐 CORS
CORS_ORIGIN=*

# 📧 Email (SMTP Hostinger)
SMTP_HOST=smtp.hostinger.com
SMTP_PORT=465
SMTP_SECURITY=ssl
SMTP_USER=support@groupegenetics.com
SMTP_PASSWORD=mot-de-passe-de-la-boite
```

### 🔑 Configuration SMTP (Hostinger)
1. Dans hPanel → Emails, récupérez les paramètres SMTP de la boîte (serveur `smtp.hostinger.com`, port `465`, SSL)
2. Renseignez `SMTP_USER` (adresse complète) et `SMTP_PASSWORD` dans le `.env`
3. `MAIL_FROM` doit être cette même adresse ou un de ses alias, sinon Hostinger refuse l'envoi
4. Les destinataires internes se règlent avec `INCIDENT_ALERT_RECIPIENTS` et `CONTACT_RECIPIENTS`

## 🎮 Utilisation

### Démarrer le Serveur
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 🌐 Accès
- **API** : http://localhost:8000
- **Documentation Swagger** : http://localhost:8000/docs
- **Documentation ReDoc** : http://localhost:8000/redoc

### 🧪 Test de Base
```bash
curl http://localhost:8000/
```

Réponse attendue :
```json
{
  "message": "Bienvenue sur l'API Groupe Genetics pour la gestion de leurs supports",
  "status": "online",
  "version": "1.0.0",
  "documentation": "/docs"
}
```

## 📚 Documentation API

### 🔐 Authentification

```bash
# Connexion
POST /auth/login
Content-Type: application/x-www-form-urlencoded

username=user@example.com&password=motdepasse
```

### 👤 Utilisateurs

```bash
# Création compte
POST /users/create-user
{
  "name": "John Doe",
  "email": "john@example.com",
  "password": "motdepasse123",
  "company": "Ma Société",
  "phone": "+33123456789"
}

# Profil utilisateur
GET /users/me
Authorization: Bearer <token>
```

### 🎫 Incidents

```bash
# Créer un incident
POST /incidents/create-incident
Authorization: Bearer <token>
{
  "title": "Problème de connexion",
  "description": "Impossible de me connecter au serveur",
  "priority": "HAUTE",
  "category": "RESEAU"
}

# Lister mes incidents
GET /incidents/list-incidents
Authorization: Bearer <token>

# Rapport CEO (admin uniquement)
POST /incidents/report-ceo
Authorization: Bearer <admin-token>
{
  "start_date": "2024-01-01",
  "end_date": "2024-12-31"
}
```

### 📞 Contact

```bash
# Message de contact
POST /contact/send-email
{
  "name": "Client",
  "email": "client@example.com",
  "subject": "Demande d'information",
  "message": "J'aimerais en savoir plus sur vos services"
}
```

## 🏗️ Architecture

```
app/
├── 📁 routers/           # Routes API organisées par domaine
│   ├── auth.py          # Authentification & login
│   ├── user.py          # Gestion utilisateurs
│   ├── incident.py      # CRUD incidents + rapports
│   └── contact.py       # Formulaire de contact
├── 📁 schemas/          # Modèles Pydantic de validation
│   ├── user.py         # Schémas utilisateur
│   ├── incident.py     # Schémas incident
│   ├── token.py        # Schémas JWT
│   └── contact.py      # Schémas contact
├── 📄 model.py         # Modèles SQLAlchemy (BDD)
├── 📄 config.py        # Configuration & variables d'env
├── 📄 oauth2.py        # Gestion JWT & permissions
├── 📄 utils.py         # Utilitaires (email, PDF, OTP)
├── 📄 postgres_connect.py # Connexion base de données
└── 📄 main.py          # Point d'entrée FastAPI
```

### 🔄 Flux de Données

1. **Utilisateur** → Inscription/Connexion → **JWT Token**
2. **Token** → Validation → **Accès aux endpoints protégés**
3. **Incident créé** → **Email automatique au support**
4. **CEO change statut** → **Email de résolution à l'utilisateur**
5. **Rapport demandé** → **PDF généré avec graphiques**

## 🔒 Sécurité

### 🛡️ Mesures Implémentées

- **Hachage bcrypt** pour tous les mots de passe
- **Tokens JWT** avec expiration configurable
- **Validation stricte** des données avec Pydantic
- **Protection CORS** configurable
- **OTP temporaire** (5min) pour réinitialisation
- **Permissions par rôle** (CEO vs utilisateur standard)

### 👑 Compte Administrateur

Les identifiants de l'administrateur sont **fixés dans le `.env`** :

```env
ADMIN_EMAIL=support@groupegenetics.com
ADMIN_PASSWORD=un-mot-de-passe-solide
ADMIN_NAME=Administrateur Genetics
```

- Au démarrage, l'API crée ce compte (déjà validé) s'il n'existe pas, ou met à jour son mot de passe s'il a changé dans le `.env`.
- Pour changer le mot de passe : modifier `ADMIN_PASSWORD` puis redémarrer l'API (`docker compose up -d`).
- Sans `ADMIN_PASSWORD`, aucun compte administrateur n'est créé (un avertissement s'affiche dans les logs).
- `ADMIN_EMAILS` (facultatif) donne aussi le rôle administrateur à d'autres adresses.
- Les adresses administrateur ne peuvent pas être utilisées pour s'inscrire depuis le site.

## 🚀 Déploiement

### 🐳 Docker (Recommandé)

Le projet fournit un `Dockerfile` (multi-stage) et un `docker-compose.yml` (API + PostgreSQL).
Voir [Démarrage rapide](#-démarrage-rapide).

```bash
docker compose up -d --build
```

### ☁️ Heroku

```bash
# Procfile
web: uvicorn app.main:app --host 0.0.0.0 --port $PORT

# Déploiement
heroku create genetics-incidents-api
git push heroku main
```

### 🔧 Variables de Production

```env
POSTGRES_URL=postgresql://prod_user:prod_pass@prod_host:5432/prod_db
SECRET_KEY=super-secure-production-key-256-bits-minimum
CORS_ORIGIN=https://yourdomain.com,https://app.yourdomain.com
```

## 📊 Monitoring & Logs

```python
# Logs disponibles avec Rich
console.print(":banana: [cyan]API starting...[/]")
console.print(":mango: [red]API shutting down...[/]")

# Endpoints de santé
GET /                    # Status API
GET /incidents/all-incidents  # Monitoring incidents (CEO)
```

## 🤝 Contribution

### 📝 Standards de Code

1. **Style** : Suivre PEP 8
2. **Type hints** : Obligatoires pour toutes les fonctions
3. **Docstrings** : Format Google style
4. **Tests** : Couverture minimale 80%

### 🔄 Workflow

1. Fork le projet
2. Créer une branche feature (`git checkout -b feature/nouvelle-fonctionnalite`)
3. Commiter les changements (`git commit -am 'Ajout fonctionnalité'`)
4. Push vers la branche (`git push origin feature/nouvelle-fonctionnalite`)
5. Créer une Pull Request

### 🧪 Tests

```bash
# Installer les dépendances de test
pip install pytest pytest-asyncio httpx

# Lancer les tests
pytest tests/ -v

# Avec couverture
pytest --cov=app tests/
```

## 📞 Support & Contact

- **🌐 Site web** : [groupegenetics.com](https://groupegenetics.com)
- **📧 Support technique** : support@groupegenetics.com
- **📧 Contact général** : contact@groupegenetics.com
- **👨‍💻 Développeur principal** : diallo30amadoukorka@gmail.com

## 📄 Licence

© 2024 **Groupe Genetics**. Tous droits réservés.

---

## 🚀 Roadmap

### Version 1.1
- [ ] Interface web admin
- [ ] Notifications push en temps réel
- [ ] API webhooks pour intégrations tierces
- [ ] Dashboard analytics avancé

### Version 1.2
- [ ] Système de SLA automatique
- [ ] Intégration Slack/Teams
- [ ] Base de connaissances intégrée
- [ ] Mobile app companion

---

**Développé avec ❤️ par l'équipe Groupe Genetics** 🧬✨
