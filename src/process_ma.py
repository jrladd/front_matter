#! /usr/bin/env python3

import csv, glob, re
from itertools import groupby
from operator import itemgetter

def clean(text):
    """
    Clean EM texts using basic regex functions. Handles uppercase words,
    long s, v to u, and vv to w.
    """
    clean_text = text.replace('\u017f', 's')
    clean_text = re.sub(r"\bI(?=[AEIOUaeiou])", "J", clean_text)
    clean_text = re.sub(r"VV|Vv|UU|Uu", "W", clean_text)
    clean_text = re.sub(r'vv|uu', 'w', clean_text)
    clean_text = re.sub(r"(v|V)(?![AEIOUaeiou])", replV, clean_text)
    clean_text = re.sub(r"\b[A-Z]+\b", titlerepl, clean_text)
    return clean_text

def titlerepl(matchobj):
    """
    Function to turn regex results to Title Case, used on uppercase words
    """
    return matchobj.group(0).title()

def replV(matchobj):
    """
    Function for dealing with capital or lowercase V's
    """
    if matchobj.group(0) == 'v':
        return 'u'
    else:
        return 'U'

if __name__ == "__main__":
    csvfiles = glob.glob('data/ma_split_outputs/*')

    for c in csvfiles[:300]:
        filename = c.split('/')[-1]
        filekey = filename.split('_')[0]
        filetype = filename.split('_')[-1].split('.')[0]
        print(filekey, filetype)
        with open(c, 'r') as csvfile:
            reader = csv.reader(csvfile, delimiter='\t')
            reader = [r for r in reader]
            for k,g in groupby(reader, key=itemgetter(2)): # Change key function to deal with all np's?
                group = [x for x in g]
                if 'np' in k and len(group) > 1:
                    name = ' '.join([x[3] for x in group])
                    clean_name = clean(name)
                    print(clean_name)
