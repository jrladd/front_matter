#! /usr/bin/env python3

import csv
from collections import Counter

with open('data/1640s_reg_weighted_curated.tsv', 'r') as csvfile:
    reader = csv.reader(csvfile, delimiter='\t')
    data = [r for r in reader]
    data = data[1:]
    cleaned = []
    for d in data:
        if len(d) != 4:
            d.append('f')
        d.append(d[1].title().replace('\u017f', 's'))
        cleaned.append(d)

cleaned_edges = [(c[0], c[2], c[3], c[4]) for c in cleaned]
counted = Counter(cleaned_edges)

aggregated = []
for k,v in counted.items():
    k = list(k)
    if v > 1:
        print(k, v)
        k[1] = '2'
    aggregated.append(k)

#aggregated_fixed = []
#for a in aggregated:
#    a[-1] = a[-1].replace('\u017f', 's')
#    aggregated_fixed.append(a)


christ = ['Jesus', 'Iesus', 'Christ ', 'Christs']
standardized = []
for a in aggregated:
    if any(c in a[-1] for c in christ) or a[-1].endswith('Christ'):
        a.append('Jesus Christ')
    standardized.append(a)

#for s in standardized:
    #print(s)

with open('data/1640s_standardized.tsv', 'w') as newcsv:
    writer = csv.writer(newcsv, delimiter='\t')
    writer.writerows(standardized)
