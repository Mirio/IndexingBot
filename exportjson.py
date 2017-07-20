# -*- coding: utf-8 -*-
from config import algolia_id, algolia_secret
import os
import sys
import json

sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)),
                             "./lib"))
from algoliasearch import algoliasearch

# Init algolia
algolia = algoliasearch.Client(algolia_id, algolia_secret)
algolia_index = algolia.init_index("groups")
res = algolia_index.search("", {"filters": 'enabled = 1', "hitsPerPage": 99999})

groups = {}
for group in res["hits"]:
    if group["category"] in groups:
        groups[group["category"]].append(group)
    else:
        groups[group["category"]] = [group]
htmlout = ''
htmlhead = ('<table class="table table-striped table-hover text-center">'
            '<thead><tr><th>Nome Gruppo</th>'
            '<th>Descrizione</th><th>Link</th></tr>'
            '</thead><tbody>')

for category in groups:
    htmlout += '<h2>%s</h2>%s' % (category, htmlhead)
    for group in groups[category]:
        htmlout += ('<tr><td>%s</td><td>%s</td><td>'
            '<a href="%s">Click</a></td></tr>') % (
            group["name"], group["desc"],
            group["url"])
    htmlout += '</tbody></table>'

print htmlout.encode("utf-8")
