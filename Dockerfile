#
# Build the d3fend-ontology docker image.
#
FROM rockylinux:9 AS src

WORKDIR /src
COPY . /src
# Ensure the path exists even if the user doesn't have a local `.local/` dir
RUN mkdir -p /src/.local

FROM rockylinux:9 AS ontology-toolchain

ARG ROBOT_URL

WORKDIR /app

# Copy optional local certs early so package installs can use them
COPY --from=src /src/.local /app/.local

# if any custom SSL certs exist in .local, install them
RUN if [ -n "$(find .local -name '*.pem' -o -name '*.crt' 2>/dev/null)" ]; then \
  echo "Copying SSL certs from .local"; \
  # if [ -e ] won't work here because of sh: Too Many Arguments
  find /app/.local -name '*.crt' -exec cp {} /etc/pki/ca-trust/source/anchors \; 2>/dev/null || true; \
  find /app/.local -name '*.pem' -exec cp {} /etc/pki/ca-trust/source/anchors \; 2>/dev/null || true; \
  update-ca-trust extract; \
fi

RUN dnf -y install python39 java-21-openjdk-headless make python3-pip which git && dnf clean all
VOLUME [ "/dist" ]
RUN pip3 install pipenv==2022.8.5

FROM ontology-toolchain AS ontology-base

ARG ROBOT_URL

# Install deps in a cache-friendly layer (only depends on Pipfile.lock/Makefile)
COPY --from=src /src/Makefile /app/Makefile
COPY --from=src /src/Pipfile /app/Pipfile
COPY --from=src /src/Pipfile.lock /app/Pipfile.lock
RUN if [ -n "${ROBOT_URL}" ]; then make ROBOT_URL="${ROBOT_URL}" clean install-deps; else make clean install-deps; fi

FROM ontology-base

COPY --from=src /src /app
#RUN make build extensions dist
RUN make all
