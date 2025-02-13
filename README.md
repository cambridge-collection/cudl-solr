# Instructions

The solr core configs and schemata are contained in `docker/data/solr/data`.

## Local Build

Ensure you have a directory called `./external-vol` at the root of this repo. This directory will contain your solr config, indices and logs. When you launch the instance, the contents of `docker/data/solr` will be copied into `./external-vol`.

    docker compose up --force-recreate --build

## AWS

1. Use the image in our private ECR
2. Mount an EFS volume directory onto `/var/solr`. The contents of `docker/data/solr` will be copied onto it when the image is mounted.

**NOTE**

`/var/solr` is the default location for solr conf/schema files. It's also where solr will write all its indices and working files.

Ideally, we'd store the schema/conf settings in a separate repository - to keep the application logic simpler.
    

## Sample queries

All queries will return the first page of results (max 20 items)

<http://localhost:8983/solr/cdcp/select?> -- retrieve all docs, the default when no query terms are given
<http://localhost:8983/solr/cdcp/select?q=greek%20empire> -- retrieve all docs with 'Greek' and 'Empire'
<http://localhost:8983/solr/cdcp/select?q=%22certain%20philosophical%20questions%22> -- retrieve all docs with the phrase "Certain Philosophical Questions". The title of a tract contained within Newton's Trinity Notebook. NB: The results are sorted by relevance but aren't in the order I would expect. The order of the results is: 'Certain Philosophical Questions' (MS Add 3996, ff 88r-135r), MS Add 3995 (various drafts and fragments - some of which resemble parts of the previous tract), MS Add 3996 itself. I would have expected 3996 to come before 3995.
