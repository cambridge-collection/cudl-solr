#!/usr/bin/env bash
# Copy core defintions/configs from /tmp/solr to EFS volume mounted on /var/solr
set -euo pipefail

cp -r /tmp/solr/. /var/solr/
