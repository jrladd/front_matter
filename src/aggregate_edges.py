#! /usr/bin/env python3

import csv
from collections import Counter

with open('data/1640s_regularized_edgelist.csv') as csvfile:
    reader = csv.reader(csvfile, delimiter='\t')
    edgelist = [tuple(r) for r in reader]

weights = Counter(edgelist)
weighted_edges = [[k[0], k[1], v] for k, v in weights.items()]
print(weighted_edges)

with open('data/1640s_reg_weighted.tsv', 'w') as newcsv:
    writer = csv.writer(newcsv, delimiter="\t")
    writer.writerows(weighted_edges)
