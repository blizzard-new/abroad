# Separate demo image. Does not change the production Dockerfile or its tag.
FROM python:3.12-slim
ARG TARGETARCH
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 PIP_NO_CACHE_DIR=1 PIP_DISABLE_PIP_VERSION_CHECK=1
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /opt/uniway
COPY pyproject.toml uv.lock README.md ./
COPY src/exchange_info/tls_trust.py ./src/exchange_info/tls_trust.py
COPY scripts/harden_image_ca.py /tmp/harden_image_ca.py
COPY deploy/cgu-demo/install_node.py /tmp/install_node.py
RUN --mount=type=secret,id=build_ca,required=false \
    if [ -f /run/secrets/build_ca ]; then export SSL_CERT_FILE=/run/secrets/build_ca; fi; \
    PYTHONPATH=src python /tmp/harden_image_ca.py /usr/share/ca-certificates \
    && update-ca-certificates --fresh \
    && python /tmp/install_node.py "$TARGETARCH"
ENV PLAYWRIGHT_NODEJS_PATH=/opt/uniway-node/bin/node
# Install dependencies before copying the large public assets so UI changes
# reuse the dependency layer.
# Optional build-only CA supports managed CI proxies without retaining their
# certificates in the image or changing runtime trust. Windows needs no secret.
RUN --mount=type=secret,id=build_ca,required=false \
    if [ -f /run/secrets/build_ca ]; then export SSL_CERT_FILE=/run/secrets/build_ca PIP_CERT=/run/secrets/build_ca; fi; \
    python -m pip install "pip @ https://files.pythonhosted.org/packages/3f/06/3e4420302363fbb71be3c7f35ce042f54bfca330e3e66b3a2e3c4cca579f/pip-26.2.2-py3-none-any.whl#sha256=fd7f4dfa8190e014013b9f08f3e973f4e4c26ffd179a204895533a7254813a70" \
    && python -m pip install uv==0.13.5
# The exported lock already resolves project constraints. Do not reapply loose
# pyproject constraints in uv's hash-checking installer.
RUN --mount=type=secret,id=build_ca,required=false \
    if [ -f /run/secrets/build_ca ]; then export SSL_CERT_FILE=/run/secrets/build_ca; fi; \
    uv export --frozen --no-dev --no-emit-project --output-file /tmp/runtime-requirements.txt > /dev/null \
    && uv --no-config pip install --system --no-cache --require-hashes -r /tmp/runtime-requirements.txt
COPY deploy/cgu-demo/verify_deployment.py /opt/demo-verify.py
# Explicit read/traverse permissions also support restrictive source checkouts.
# Root owns this tree; the runtime user cannot edit it. Editable installation
# avoids a second copy of several GiB of public assets.
COPY --chmod=0755 src ./src
RUN --mount=type=secret,id=build_ca,required=false \
    if [ -f /run/secrets/build_ca ]; then export SSL_CERT_FILE=/run/secrets/build_ca PIP_CERT=/run/secrets/build_ca; fi; \
    python -m pip install --no-deps -e . \
    && unset SSL_CERT_FILE PIP_CERT \
    && python -m exchange_info.tls_audit --system \
    && chmod a+r /opt/demo-verify.py \
    && useradd --system --uid 10001 --create-home uniway
ARG APP_REVISION=working-tree
ENV CGU_DEMO_REVISION=$APP_REVISION
LABEL org.opencontainers.image.revision=$APP_REVISION
USER uniway
WORKDIR /home/uniway
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=10s --start-period=180s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=8)"
CMD ["uvicorn", "exchange_info.cgu_demo:create_demo_app", "--factory", "--host", "0.0.0.0", "--port", "8000", "--workers", "1", "--no-proxy-headers"]
