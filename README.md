# Instructions

1. Place solr json files in ./data/json/
1. docker compose up -d --build
1. Index files, e.g. `find /var/json -name '*.json' -exec /opt/solr/bin/post -c cdcp -params "split=/pages" {} \;` to index everything. This will likely take about 25 minutes. MS-ADD-*.xml makes a nice sample to do. It contains a wide variety of items but indexes quickly enough.

## Sample queries

All queries will return the first page of results (max 20 items)

<http://localhost:8983/solr/cdcp/select?> -- retrieve all docs, the default when no query terms are given
<http://localhost:8983/solr/cdcp/select?q=greek%20empire> -- retrieve all docs with 'Greek' and 'Empire'
<http://localhost:8983/solr/cdcp/select?q=%22certain%20philosophical%20questions%22> -- retrieve all docs with the phrase "Certain Philosophical Questions". The title of a tract contained within Newton's Trinity Notebook. NB: The results are sorted by relevance but aren't in the order I would expect. The order of the results is: 'Certain Philosophical Questions' (MS Add 3996, ff 88r-135r), MS Add 3995 (various drafts and fragments - some of which resemble parts of the previous tract), MS Add 3996 itself. I would have expected 3996 to come before 3995.