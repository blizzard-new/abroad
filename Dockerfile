# The web service, for running on your own computer (see deploy/selfhost/README.md).
# Render does not use this file: it builds with `pip install .` (render.yaml).
FROM python:3.12-slim

# The distro may lag CA removals; exact incident anchors are filtered below.
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates \
 && rm -rf /var/lib/apt/lists/*

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /build
COPY pyproject.toml uv.lock README.md ./
COPY src ./src
# Bootstrap using the PSF-recommended hash-pinned wheel, before any unpinned download.
RUN python -m pip install "pip @ https://files.pythonhosted.org/packages/3f/06/3e4420302363fbb71be3c7f35ce042f54bfca330e3e66b3a2e3c4cca579f/pip-26.2.2-py3-none-any.whl#sha256=fd7f4dfa8190e014013b9f08f3e973f4e4c26ffd179a204895533a7254813a70" \
 && python -m pip install uv==0.13.5 \
 && uv export --frozen --no-dev --no-emit-project --output-file /tmp/runtime-requirements.txt \
 && python -m pip install --require-hashes -r /tmp/runtime-requirements.txt \
 && python -m pip install --no-deps .

COPY scripts/harden_image_ca.py /build/harden_image_ca.py
RUN python /build/harden_image_ca.py /usr/share/ca-certificates \
 && update-ca-certificates --fresh \
 && python -m exchange_info.tls_audit --system

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
