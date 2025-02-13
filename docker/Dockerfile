ARG SOLR_VERSION=9

FROM solr:${SOLR_VERSION:?}
# Copy schemata and configs for CUDL cores to tmp directory
COPY --chown=solr --chmod=ug+w ./data/solr /tmp/solr

# Add script that copies cores from /tmp/solr to /var/solr to directory
# that contains script that are run before solr is started.
COPY --chmod=755 ./scripts/copy-cores.sh /docker-entrypoint-initdb.d/
#RUN chown -R solr /var/solr && chmod -R ug+w /var/solr
USER solr
