#
# Build the d3fend-ontology docker image.
#
FROM rockylinux:9

ARG ROBOT_URL

COPY . /app
WORKDIR /app

# if any custom SSL certs exist in .local, install them
RUN if [ -n "$(find .local -name '*.pem' -o -name '*.crt' 2>/dev/null)" ]; then \
  echo "Copying SSL certs from .local"; \
  # if [ -e ] won't work here because of sh: Too Many Arguments
  find /app/.local -name '*.crt' -exec cp {} /etc/pki/ca-trust/source/anchors \; 2>/dev/null || true; \
  find /app/.local -name '*.pem' -exec cp {} /etc/pki/ca-trust/source/anchors \; 2>/dev/null || true; \
  update-ca-trust extract; \
fi

RUN dnf -y install python39 java-17-openjdk-headless make python3-pip which git
VOLUME [ "/dist" ]
RUN pip3 install pipenv==2022.8.5
RUN make ROBOT_URL=${ROBOT_URL} clean install-deps
RUN make build extensions dist
