# Upstream's server, with Google Static Maps swapped for keyless OSM tiles.
#
# Everything else — the HTML/CSS page layouts, Chart.js, rough.js, Selenium and
# the headless Chromium that screenshots them — remains upstream's.
# The Google adapter removes the billing dependency; the retry adapter handles
# transient generation failures.
FROM ghcr.io/chrisjtwomey/inkplate10-weather-cal-server:latest

USER root

# Our map code, shared with the Pillow renderer in ../server.
COPY server/mapview.py /app/nook_mapview.py
COPY server/linemap.py /app/linemap.py
COPY server/fonts.py /app/fonts.py
COPY upstream/google_api_shim.py /app/google/api.py

RUN chown -R app:app /app/google /app/nook_mapview.py /app/linemap.py /app/fonts.py

COPY upstream/retrying_server.py /app/retrying_server.py
RUN sed -i "s/from epd_server import DisplayServer, align_process_timezone/from epd_server import align_process_timezone\nfrom retrying_server import DisplayServer/" /app/server.py

USER app
