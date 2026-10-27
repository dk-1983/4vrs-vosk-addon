# Dependency runtime: Vosk 0.3.45 + Wyoming 1.5.2, matching the tested Vosk engine.
# Upstream image and its bundled third-party packages retain their licenses.
FROM rhasspy/wyoming-vosk:1.5.1@sha256:18517f4c588e8b39f3d0a31233e2d97df33eefd729ebc4e51ac03f92b4265299
ARG BUILD_ARCH=amd64
ARG BUILD_VERSION=0.1.0
LABEL io.hass.name="4VRS Vosk" \
      io.hass.description="Unofficial Vosk speech recognition app with Wyoming support" \
      io.hass.type="addon" \
      io.hass.version="${BUILD_VERSION}" \
      io.hass.arch="${BUILD_ARCH}" \
      org.opencontainers.image.source="https://github.com/dk-1983/4vrs-vosk-addon"
ENV PYTHONUNBUFFERED=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
WORKDIR /app
COPY app/ /app/
COPY licenses/ /app/licenses/
HEALTHCHECK --interval=30s --timeout=5s --start-period=30m --retries=3 CMD ["python3", "/app/healthcheck.py"]
ENTRYPOINT ["python3", "/app/main.py"]
