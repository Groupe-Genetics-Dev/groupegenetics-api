#!/usr/bin/env bash
# Installation de la plateforme Groupe Genetics (API + site) sur un serveur Ubuntu.
# Usage, sur le serveur :
#   curl -fsSLO https://raw.githubusercontent.com/Groupe-Genetics-Dev/groupegenetics-api/main/deploy/install.sh
#   bash install.sh [adresse-publique]      (par défaut : l'IP publique du serveur)
# Relancer le script met à jour le code et redémarre les services sans toucher aux fichiers .env existants.
set -euo pipefail

ORG=https://github.com/Groupe-Genetics-Dev
HOST="${1:-$(curl -fsS https://checkip.amazonaws.com | tr -d '[:space:]')}"
echo "==> Adresse publique : $HOST"

# Remplace (ou ajoute) KEY=valeur dans un fichier .env, sans interpréter les caractères spéciaux de la valeur
set_env() {
  V="$3" awk -v k="$2" 'BEGIN { v = ENVIRON["V"] } $0 ~ "^" k "=" { print k "=" v; done = 1; next } { print } END { if (!done) print k "=" v }' "$1" >"$1.tmp"
  mv "$1.tmp" "$1"
}

ask() { # ask <variable> <question> [secret]  (une réponse vide n'est acceptée que pour les questions non secrètes)
  local answer
  while :; do
    if [ "${3:-}" = secret ]; then read -rsp "$2 : " answer </dev/tty; echo; else read -rp "$2 : " answer </dev/tty; fi
    [ -n "$answer" ] || [ "${3:-}" != secret ] && break
    echo "   La réponse ne peut pas être vide."
  done
  printf -v "$1" '%s' "$answer"
}

# 1. Docker
if ! command -v docker >/dev/null 2>&1; then
  echo "==> Installation de Docker"
  curl -fsSL https://get.docker.com | sudo sh
  sudo usermod -aG docker "$USER"
fi
DOCKER=docker
docker info >/dev/null 2>&1 || DOCKER="sudo docker"

# 2. Mémoire d'échange : la construction du site échoue avec moins de 2 Go de mémoire
if [ -z "$(swapon --show)" ] && [ "$(awk '/MemTotal/ { print $2 }' /proc/meminfo)" -lt 2000000 ]; then
  echo "==> Ajout de 2 Go de mémoire d'échange"
  sudo fallocate -l 2G /swapfile
  sudo chmod 600 /swapfile
  sudo mkswap /swapfile >/dev/null
  sudo swapon /swapfile
  grep -q '^/swapfile' /etc/fstab || echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab >/dev/null
fi

# 3. Code
cd "$HOME"
for repo in groupegenetics-api groupegenetics-front; do
  if [ -d "$repo/.git" ]; then
    echo "==> Mise à jour de $repo"
    git -C "$repo" pull --ff-only
  else
    echo "==> Téléchargement de $repo"
    git clone "$ORG/$repo.git"
  fi
done

# 4. Configuration de l'API (seulement à la première installation)
cd "$HOME/groupegenetics-api"
if [ ! -f .env ]; then
  echo "==> Configuration de l'API (évitez le caractère \$ dans les mots de passe)"
  ask ADMIN_PASSWORD "Mot de passe du compte admin (support@groupegenetics.com)" secret
  ask SMTP_USER "Boîte e-mail d'envoi [mohamed.thialaw@groupegenetics.com]"
  SMTP_USER="${SMTP_USER:-mohamed.thialaw@groupegenetics.com}"
  ask SMTP_PASSWORD "Mot de passe de la boîte $SMTP_USER" secret

  DB_PASSWORD="$(openssl rand -hex 16)"
  cp .env.example .env
  set_env .env POSTGRES_PASSWORD "$DB_PASSWORD"
  set_env .env POSTGRES_URL "postgresql://genetics:$DB_PASSWORD@db:5432/genetics_incidents"
  set_env .env SECRET_KEY "$(openssl rand -hex 32)"
  set_env .env ADMIN_PASSWORD "$ADMIN_PASSWORD"
  set_env .env SMTP_USER "$SMTP_USER"
  set_env .env SMTP_PASSWORD "$SMTP_PASSWORD"
  set_env .env MAIL_FROM "$SMTP_USER"
  set_env .env SITE_LOGIN_URL "http://$HOST/support/login"
  set_env .env ADMIN_ACCOUNTS_URL "http://$HOST/support/admin/accounts"
  # La base de données n'est joignable que depuis le serveur
  set_env .env DB_PORT "127.0.0.1:5432"
  chmod 600 .env
fi

# 5. Configuration du site
cd "$HOME/groupegenetics-front"
if [ ! -f .env ]; then
  printf 'NEXT_PUBLIC_API_URL=http://%s:8000\nNEXT_PUBLIC_SITE_URL=http://%s\nFRONT_PORT=80\n' "$HOST" "$HOST" >.env
fi

# 6. Démarrage
echo "==> Démarrage de l'API"
cd "$HOME/groupegenetics-api" && $DOCKER compose up -d --build
echo "==> Construction et démarrage du site (5 à 10 minutes sur un petit serveur)"
cd "$HOME/groupegenetics-front" && $DOCKER compose up -d --build

echo "==> Test d'envoi des e-mails"
cd "$HOME/groupegenetics-api"
sleep 5
$DOCKER compose exec -T api python -m app.mailer || echo "!! Envoi d'e-mails à vérifier (SMTP_USER / SMTP_PASSWORD dans ~/groupegenetics-api/.env)"

cat <<DONE

Installation terminée :
  Site      : http://$HOST
  Connexion : http://$HOST/support/login
  API       : http://$HOST:8000/docs
Ports à ouvrir dans le groupe de sécurité AWS : 22, 80 et 8000.
DONE
