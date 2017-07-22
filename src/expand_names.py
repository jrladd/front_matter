#! /usr/bin/env python3

import csv
from collections import Counter

with open('data/1640s_reg_weighted_curated.tsv', 'r') as csvfile:
    reader = csv.reader(csvfile, delimiter='\t')
    data = [r for r in reader]
    cleaned = []
    for d in data:
        if len(d) != 4:
            d.append('f')
        d.append(d[1].title())
        cleaned.append(d)

#for c in cleaned:
    #print(c)

cleaned_edges = [(c[0], c[-1]) for c in cleaned]
counted = Counter(cleaned_edges)

for k,v in counted.items():
    if v > 1:
        print(k,v)
