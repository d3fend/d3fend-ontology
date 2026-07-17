#!/bin/bash
set -euo pipefail

# Wrapper purpose:
# ROBOT currently emits noisy JDK unsafe/deprecated-method warnings on stderr.
# Keep this wrapper only until ROBOT fixes:
# https://github.com/ontodev/robot/issues/1263
# When that issue is fixed in the ROBOT version used by this repo, remove this
# script and restore the Makefile to write the simple `java -jar robot.jar "$@"`
# launcher directly.

ROBOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
JAVA_BIN="${ROBOT_JAVA:-java}"
JAVA_OPTS=()

if [ -n "${ROBOT_JAVA_OPTS:-}" ]; then
  read -r -a EXTRA_JAVA_OPTS <<< "$ROBOT_JAVA_OPTS"
  JAVA_OPTS+=("${EXTRA_JAVA_OPTS[@]}")
fi

if [ "${ROBOT_SUPPRESS_UNSAFE_WARNINGS:-true}" = "true" ]; then
  STDERR_FILE="$(mktemp "${TMPDIR:-/tmp}/robot-stderr.XXXXXX")"
  trap 'rm -f "$STDERR_FILE"' EXIT

  set +e
  "$JAVA_BIN" ${JAVA_OPTS[@]+"${JAVA_OPTS[@]}"} \
    -jar "$ROBOT_DIR/robot.jar" "$@" 2> "$STDERR_FILE"
  STATUS="$?"
  set -e

  awk '
    /^WARNING: A terminally deprecated method in sun[.]misc[.]Unsafe has been called$/ { next }
    /^WARNING: sun[.]misc[.]Unsafe::[[:alnum:]_]+ has been called by / { next }
    /^WARNING: Please consider reporting this to the maintainers of class / { next }
    /^WARNING: sun[.]misc[.]Unsafe::[[:alnum:]_]+ will be removed in a future release$/ { next }
    { print > "/dev/stderr" }
  ' "$STDERR_FILE"

  exit "$STATUS"
fi

exec "$JAVA_BIN" ${JAVA_OPTS[@]+"${JAVA_OPTS[@]}"} \
  -jar "$ROBOT_DIR/robot.jar" "$@"
