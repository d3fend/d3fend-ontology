#
# Build the d3fend-ontology docker image.
#
FROM rockylinux:latest

ARG ROBOT_URL
RUN dnf -y install python38 java-17-openjdk-headless make
VOLUME [ "/dist" ]
RUN pip3 install pipenv
COPY . /app
WORKDIR /app
RUN make ROBOT_URL=${ROBOT_URL} clean install-deps
ENTRYPOINT [ "make", "build" ]
