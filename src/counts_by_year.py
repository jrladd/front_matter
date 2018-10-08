#! /usr/bin/env python

import json
from collections import defaultdict

with open("../docs/all_eebo.json", "r") as jsonfile:
    network = json.loads(jsonfile.read())

nodes = [n for n in network['nodes'] if n["id"].startswith("A") == False and n["id"].startswith("B") == False]
links = network['links']

no_year = []
text_year = {}
for n in network['nodes']:
    try:
        if n["date"] != None:
            text_year[n["id"]] = n["date"]
    except KeyError:
        no_year.append((n["id"]))
print(no_year, len(no_year))
print(len(text_year))
counts_by_year = []
for n in nodes:
    count_dict = {}
    node_id = n['id']
    name_variants = n["name_variants"]
    count_dict["id"] = node_id
    count_dict["name_variants"] = n["name_variants"]
    count_dict["values"] = defaultdict(int)
    for l in links:
        if node_id == l['source']:
            if l['target'] in text_year.keys():
                # print(text_year[l["target"]], l["weight"])
                count_dict["values"][text_year[l["target"]]] += l["weight"]
        elif node_id == l['target']:
            if l['source'] in text_year.keys():
                # print(text_year[l["source"]], l["weight"])
                count_dict["values"][text_year[l["source"]]] += l["weight"]
    count_dict["values"] = [{"year":k, "count":v} for k,v in count_dict["values"].items()]
    counts_by_year.append(count_dict)

# print(counts_by_year)

with open("../docs/counts_by_year.json", "w") as output:
    json.dump(counts_by_year, output, sort_keys=True, indent=4, separators=(',',':'))
