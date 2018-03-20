#! /usr/bin/env python3

import csv, glob
from itertools import groupby
from operator import itemgetter

csvfiles = glob.glob('data/ma_outputs/*')

for c in csvfiles[:10]:
    with open(c, 'r') as csvfile:
        reader = csv.reader(csvfile, delimiter='\t')
        reader = [r for r in reader]
        # for i,r in enumerate(reader):
        #     if 'np' in r[2] and '.' not in r[0]:
        #         # print(r[0],r[2])
        #         try:
        #             if 'np' in reader[i+1][2]: #and '.' not in r[i+1][0]:
        #                 print(r[0]+' '+reader[i+1][0])
        #             # else:
        #             #     print(r[0])
        #         except IndexError:
        #             pass
        for k,g in groupby(reader, key=itemgetter(2)):
            group = [x for x in g]
            if 'np' in k and len(group) > 1:
                print(k, ' '.join([x[0] for x in group]))
