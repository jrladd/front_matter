#! /usr/bin/env python3

import csv, glob
from itertools import groupby
from operator import itemgetter

csvfiles = glob.glob('data/ma_outputs/*')

for c in csvfiles[:10]:
    with open(c, 'r') as csvfile:
        reader = csv.reader(csvfile, delimiter='\t')
        reader = [r for r in reader]
        for k,g in groupby(reader, key=itemgetter(2)):
            group = [x for x in g]
            if 'np' in k and len(group) > 1:
                print(k, ' '.join([x[0] for x in group]))
