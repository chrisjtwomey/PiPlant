#!/usr/bin/env bash

set -ex

apt-get update && apt-get install -y vim && rm -rf /var/lib/apt/lists/*
python3 -m pip install -r ./.devcontainer/requirements-dev.txt
pre-commit install --config ./.devcontainer/.pre-commit-config.yaml