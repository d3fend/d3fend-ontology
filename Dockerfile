#
# Build the d3fend-ontology docker image.
#
FROM rockylinux:9

ARG ROBOT_URL

RUN dnf -y install python39 java-17-openjdk-headless make python3-pip which git
VOLUME [ "/dist" ]
RUN pip3 install pipenv==2022.8.5
COPY . /app
WORKDIR /app
RUN make ROBOT_URL=${ROBOT_URL} clean install-deps
RUN make build extensions dist
