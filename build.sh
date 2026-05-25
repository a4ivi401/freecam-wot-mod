#!/usr/bin/env bash
set -eu

ROOT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
cd "$ROOT_DIR"

if [ $# -gt 0 ]; then
  VERSION="$1"
elif [ -n "${GITHUB_REF_NAME:-}" ]; then
  VERSION="${GITHUB_REF_NAME#v}"
else
  VERSION="$(sed -n 's:.*<version>\(.*\)</version>.*:\1:p' meta.xml | head -n 1 | tr -d '[:space:]')"
fi

if [ -z "$VERSION" ]; then
  echo "Could not determine version." >&2
  exit 1
fi

python pack_mtmod.py "$VERSION"
