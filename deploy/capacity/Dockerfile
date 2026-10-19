# syntax=docker/dockerfile:1
FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 PIP_NO_CACHE_DIR=1 PIP_DISABLE_PIP_VERSION_CHECK=1
COPY pyproject.toml README.md /build/
COPY deploy/selfhost/docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod 0755 /usr/local/bin/docker-entrypoint.sh \
 && useradd --system --uid 10001 --create-home uniway \
 && mkdir -p /usr/local/lib/python3.12/data \
 && chown -R uniway:uniway /usr/local/lib/python3.12/data
WORKDIR /home/uniway
# Source documents are large. BuildKit's temporary writable bind permits setuptools
# metadata without retaining a second source tree or build directory in the image.
# A cloud proxy CA can be supplied as a secret; it never enters an image layer.
RUN --mount=type=bind,source=src,target=/build/src,rw \
    --mount=type=secret,id=proxy_ca \
    if [ -s /run/secrets/proxy_ca ]; then export PIP_CERT=/run/secrets/proxy_ca; fi; \
    pip install /build httpx==0.28.1 && rm -rf /build/build /build/*.egg-info
USER uniway
ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
