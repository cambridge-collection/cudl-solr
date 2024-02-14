ARG SOLR_VERSION=9

FROM solr:${SOLR_VERSION:?}
#COPY --chown=solr --chmod=ug+w ./data/solr /var/solr
#COPY ./data/json /var/json
RUN chown -R solr /var/solr && chmod -R ug+w /var/solr
USER solr
