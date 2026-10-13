#!/usr/bin/env bash
# Active le HTTPS (certificats Let's Encrypt automatiques via Caddy) après install.sh.
# Prérequis : les enregistrements DNS A de DOMAINE, www.DOMAINE et api.DOMAINE pointent vers ce serveur,
# et les ports 80 et 443 sont ouverts dans le groupe de sécurité.
# Usage : bash enable-https.sh groupegenetics.com
set -euo pipefail

DOMAIN="${1:?Usage : bash enable-https.sh votre-domaine.com}"
DOCKER=docker
docker info >/dev/null 2>&1 || DOCKER="sudo docker"

set_env() {
  V="$3" awk -v k="$2" 'BEGIN { v = ENVIRON["V"] } $0 ~ "^" k "=" { print k "=" v; done = 1; next } { print } END { if (!done) print k "=" v }' "$1" >"$1.tmp"
  mv "$1.tmp" "$1"
}

# 1. Vérification DNS : sans elle, la demande de certificat échoue.
# On interroge directement les serveurs DNS du domaine (comme Let's Encrypt) : les résolveurs, y compris
# celui du serveur, peuvent garder une ancienne valeur en cache pendant des heures après une modification.
IP="$(curl -fsS https://checkip.amazonaws.com | tr -d '[:space:]')"
command -v dig >/dev/null 2>&1 || sudo apt-get install -y -qq bind9-dnsutils >/dev/null
NS="$(dig +short NS "$DOMAIN" | head -1)"
resolve() { dig +short A "$1" ${NS:+@"$NS"} | grep -E '^[0-9.]+$' | tail -1; }
for name in "$DOMAIN" "www.$DOMAIN" "api.$DOMAIN"; do
  resolved="$(resolve "$name")"
  if [ "$resolved" != "$IP" ]; then
    echo "!! $name pointe vers '${resolved:-rien}' au lieu de $IP : corrigez le DNS puis relancez." >&2
    exit 1
  fi
done
echo "==> DNS correct : $DOMAIN, www.$DOMAIN et api.$DOMAIN -> $IP"

# 2. API et site écoutent uniquement en local : Caddy les sert en HTTPS
cd "$HOME/groupegenetics-api"
set_env .env API_PORT "127.0.0.1:8000"
set_env .env SITE_LOGIN_URL "https://$DOMAIN/support/login"
set_env .env ADMIN_ACCOUNTS_URL "https://$DOMAIN/support/admin/accounts"
$DOCKER compose up -d

cd "$HOME/groupegenetics-front"
set_env .env NEXT_PUBLIC_API_URL "https://api.$DOMAIN"
set_env .env NEXT_PUBLIC_SITE_URL "https://$DOMAIN"
set_env .env FRONT_PORT "127.0.0.1:3001"
echo "==> Reconstruction du site avec l'adresse https://api.$DOMAIN (quelques minutes)"
$DOCKER compose up -d --build

# 3. Caddy : HTTPS automatique, redirection HTTP -> HTTPS
mkdir -p "$HOME/proxy" && cd "$HOME/proxy"
cat >Caddyfile <<CADDY
$DOMAIN, www.$DOMAIN {
	reverse_proxy 127.0.0.1:3001
}

api.$DOMAIN {
	reverse_proxy 127.0.0.1:8000
}
CADDY
cat >docker-compose.yml <<'COMPOSE'
services:
  caddy:
    image: caddy:2-alpine
    container_name: caddy
    restart: unless-stopped
    network_mode: host
    volumes:
      - ./Caddyfile:/etc/caddy/Caddyfile:ro
      - caddy_data:/data
      - caddy_config:/config
volumes:
  caddy_data:
  caddy_config:
COMPOSE
$DOCKER compose up -d
$DOCKER compose exec -T caddy caddy reload --config /etc/caddy/Caddyfile 2>/dev/null || true

echo "==> Obtention des certificats..."
for _ in $(seq 1 30); do
  # --resolve : teste ce serveur directement, quel que soit le cache DNS local
  if curl -fsS -o /dev/null --resolve "api.$DOMAIN:443:127.0.0.1" "https://api.$DOMAIN/docs" 2>/dev/null &&
    curl -fsS -o /dev/null --resolve "$DOMAIN:443:127.0.0.1" "https://$DOMAIN" 2>/dev/null; then
    cat <<DONE

HTTPS activé :
  Site      : https://$DOMAIN
  Connexion : https://$DOMAIN/support/login
  API       : https://api.$DOMAIN/docs
Le port 8000 peut maintenant être retiré du groupe de sécurité (garder 22, 80 et 443).
DONE
    exit 0
  fi
  sleep 5
done
echo "!! Les certificats ne sont pas encore prêts. Consultez : cd ~/proxy && $DOCKER compose logs caddy" >&2
exit 1
