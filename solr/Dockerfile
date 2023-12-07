ARG SOLR_VERSION=9

FROM solr:${SOLR_VERSION:?}
COPY --chown=solr --chmod=ug+w ./data/solr /var/solr
COPY ./data/json /var/json
#COPY --chmod=755 ./solr/context/populate-index.sh /docker-entrypoint-initdb.d/
RUN chown -R solr /var/solr && chmod -R ug+w /var/solr
#RUN test -f /var/solr/data/esawyer/conf/solrconfig.xml
USER solr
