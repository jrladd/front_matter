#! /usr/bin/env python3

import csv, re

lord = ["Lord", "lord", "lady", "Lady"]

lord_corrections = []
with open('data/1640s_regularized_edgelist.csv', 'r') as csvfile:
    reader = csv.reader(csvfile, delimiter='\t')
    rows = [r for r in reader]
    for row in rows[1:]:
        if any(l in row[1] for l in lord):
            regex = re.compile('\\w*\\W*\\w*\\W*\\w*\\W*\\w*\\W*\\w*\\W*'+row[1]+'\\W*\\w*\\W*\\w*\\W*\\w*\\W*\\w*\\W*\\w*\\W*\\w*')
            with open('data/1640s_regularized/'+row[0]+'-0.txt', 'r') as textfile:
                text = textfile.read()
                try:
                    match = regex.search(text)
                    lord_corrections.append((row[0], row[1], match.group(0)))
                except AttributeError:
                    with open('data/1640s_regularized/'+row[0]+'-1.txt', 'r') as textfile:
                            text = textfile.read()
                            try:
                                match = regex.search(text)
                                lord_corrections.append((row[0], row[1], match.group(0)))
                            except AttributeError:
                                pass

with open('data/1640s_standardized.tsv') as s_csv:
    reader = csv.reader(s_csv, delimiter='\t')
    new_rows = []
    found = []
    for r in reader:
        for l in lord_corrections:
            if [r[0], r[3]] == [l[0], l[1].title().replace('\u017f', 's')]:
                found.append(r)
                if len(r) == 4:
                    r.extend(['', l[2]])
                else:
                    r.append(l[2])
                if r not in new_rows:
                    new_rows.append(r)
            elif r not in new_rows and r not in found:
                new_rows.append(r)

for n in new_rows:
    print(n)

print(len(new_rows))
with open('data/1640s_expanded.csv', 'w') as newcsv:
    writer = csv.writer(newcsv, delimiter='\t')
    writer.writerows(new_rows)
