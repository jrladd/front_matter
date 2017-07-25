#! /usr/bin/env python3

import csv, re

lord = ["Lord", "lord"]

with open('data/1640s_regularized_edgelist.csv', 'r') as csvfile:
    reader = csv.reader(csvfile, delimiter='\t')
    rows = [r for r in reader]
    for row in rows[1:]:
        if any(l in row[1] for l in lord):
            regex = re.compile('\\w*\\W*\\w*\\W*\\w*\\W*\\w*\\W*'+row[1]+'\\W*\\w*\\W*\\w*\\W*\\w*\\W*\\w*\\W*\\w*')
            with open('data/1640s_regularized/'+row[0]+'-0.txt', 'r') as textfile:
                text = textfile.read()
                try:
                    match = regex.search(text)
                    print(row)
                    print(match.group(0))
                    #i = words.index(row[1].split()[0])
                    #print(row)
                    #print(' '.join(words[i-7:i+7]))
                except AttributeError:
                    with open('data/1640s_regularized/'+row[0]+'-1.txt', 'r') as textfile:
                            text = textfile.read()
                            try:
                                match = regex.search(text)
                                print(row)
                                print(match.group(0))
                            except AttributeError:
                                pass
