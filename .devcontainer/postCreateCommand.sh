#!/usr/bin/env bash

set -ex

apt-get update && apt-get install -y vim && rm -rf /var/lib/apt/lists/*
python3 -m pip install -r ./.devcontainer/dev-requirements.txt