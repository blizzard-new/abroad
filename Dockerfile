# The web service, for running on your own computer (see deploy/selfhost/README.md).
# Render does not use this file: it builds with `pip install .` (render.yaml).
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /build
COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install .

COPY deploy/selfhost/docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod 0755 /usr/local/bin/docker-entrypoint.sh

# The program looks for a data folder next to the installed package; production mode keeps nothing in it,
# but the folder has to exist and be writable by the user the service runs as.
RUN useradd --system --uid 10001 --create-home uniway \
 && mkdir -p /usr/local/lib/python3.12/data /home/uniway/seo-state \
 && chown -R uniway:uniway /usr/local/lib/python3.12/data /home/uniway/seo-state

USER uniway
WORKDIR /home/uniway
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=10s --start-period=120s --retries=3 \
  CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=8).status == 200 else 1)"
ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
CMD ["uvicorn", "exchange_info.api:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1", "--no-proxy-headers"]
