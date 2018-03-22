#! /usr/bin/env python3

import csv
from collections import Counter

with open('data/1640s_expanded_curated_openrefine.tsv', 'r') as csvfile:
    reader = csv.reader(csvfile, delimiter='\t')
    address = [r[3] for r in reader if r[2] == 'f']

address_list = [[k,v] for k,v in Counter(address).items() if v > 1]
print(address_list)

with open('viz/forms_of_address.csv', 'w') as newcsv:
    writer = csv.writer(newcsv, delimiter='\t')
    writer.writerows(address_list)
