#! /usr/bin/env python3

import csv
from collections import Counter

i_to_j = ['Iohn', 'Iames']
with open("data/1640s_expanded_curated_openrefine.tsv", 'r') as csvfile:
    reader = csv.reader(csvfile, delimiter='\t')
    new_list = []
    for r in reader:
        if len(r) > 4 and r[-1] != '':
            r[3] = 'Robert Devereux'
            r[-1] = ''
        #if any(x in r[4] for x in i_to_j):
        r[3].replace('Iohn', 'John')
        r[3].replace('Iames', 'James')

        new_list.append(r)

cleaned = [[l for l in n if l != ''] for n in new_list]

cleaned_tuples = [tuple(c) for c in cleaned]
counted = Counter(cleaned_tuples)

aggregated = []
for k,v in counted.items():
    k = list(k)
    if v > 1:
        print(k, v)
        k[1] = v*int(k[1])
        print(k, v)

    aggregated.append(k)
