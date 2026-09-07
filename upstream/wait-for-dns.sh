#!/usr/bin/env sh
# Block until a hostname resolves, or give up after a couple of minutes.
#
# NetworkManager-wait-online reports the network up when the link associates —
# about two seconds on a Wi-Fi Pi — which is well before DNS answers. The
# renderer geocodes its location at startup and exits on the first URLError, so
# systemd needs to hold it back until name resolution actually works.
#
# Always exits 0: an offline boot should still start the service, which then
# retries on its own, rather than blocking the unit forever.
HOST="${1:-api.open-meteo.com}"
TRIES="${2:-60}"

n=0
while [ "$n" -lt "$TRIES" ]; do
    if getent hosts "$HOST" >/dev/null 2>&1; then
        exit 0
    fi
    n=$((n + 1))
    sleep 2
done

echo "wait-for-dns: $HOST did not resolve after $((TRIES * 2))s; starting anyway" >&2
exit 0
