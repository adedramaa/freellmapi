# Build target: linux/amd64; project tested only with one replica.
FROM ubuntu:24.04
ENV DEBIAN_FRONTEND=noninteractive PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 python3-venv ca-certificates curl fontconfig libfreetype6 \
    && rm -rf /var/lib/apt/lists/*
ARG DESIGNCRAFT_VERSION=0.14.0
RUN curl --fail --silent --show-error --location --retry 3 \
    "https://github.com/storytold/designcraft/releases/download/v${DESIGNCRAFT_VERSION}/designcraft-${DESIGNCRAFT_VERSION}-linux-x86_64.deb" \
    --output /tmp/designcraft.deb && \
    (dpkg -i /tmp/designcraft.deb || (apt-get update && apt-get install -f -y --no-install-recommends)) && \
    test -x /usr/bin/designcraft-cli && \
    /usr/bin/designcraft-cli --help >/dev/null && \
    rm -f /tmp/designcraft.deb && rm -rf /var/lib/apt/lists/*
RUN python3 -m venv /venv
ENV PATH="/venv/bin:${PATH}"
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt
COPY server.py /app/server.py
RUN mkdir -p /workspace/inputs /workspace/output && chmod -R 700 /workspace
WORKDIR /app
EXPOSE 8080
CMD ["sh", "-c", "exec uvicorn server:app --host 0.0.0.0 --port ${PORT:-8080} --workers 1"]