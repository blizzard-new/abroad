#!/bin/sh
# Start-up of the web service inside Docker: make the program trust the internal gateway's certificate authority,
# in addition to the normal public ones (it also talks to Google and to official school sites over HTTPS).
set -e

CA="${INTERNAL_CA_FILE:-}"
if [ -n "$CA" ]; then
  n=0
  while [ ! -s "$CA" ] && [ "$n" -lt 60 ]; do
    n=$((n + 1))
    sleep 1
  done
  if [ ! -s "$CA" ]; then
    echo "docker-entrypoint: the gateway's CA certificate never appeared at $CA" >&2
    exit 1
  fi
  PUBLIC_CAS="$(python -c 'import certifi; print(certifi.where())')"
  cat "$PUBLIC_CAS" "$CA" > /tmp/ca-bundle.pem
  export REQUESTS_CA_BUNDLE=/tmp/ca-bundle.pem SSL_CERT_FILE=/tmp/ca-bundle.pem
fi

exec "$@"
