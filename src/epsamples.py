#! /usr/bin/env python3

##############################################
# This file created random samples based on functions in epnames.py
# It was used for verifying the precision and recall of name
# detection in epnames.py.

# The relevant information from these samples was recorded in data/count.txt
##############################################
from random import choice, sample
import csv, re
from lxml import etree
from collections import Counter, defaultdict
from colorama import init, Fore, Back, Style
from epnames import is_name

# Create a list of relevant textIds based on current data

with open('test_edges0817.csv', 'r') as csvfile:
    reader = csv.reader(csvfile, delimiter="\t")
    edges = [r for r in reader]

names_by_text = defaultdict(list)
for e in edges:
    names_by_text[e[0]].append(e[1])

names_by_text = {k:Counter(v) for k,v in names_by_text.items()}

textids = list(names_by_text.keys())

# Initialize colorama and prepare to parse EarlyPrint XML

init()
nsmap={'tei': 'http://www.tei-c.org/ns/1.0', 'ep': 'http://earlyprint.org/ns/1.0'}
parser = etree.XMLParser(collect_ids=False)

text_sample = sample(textids, 100) # Create a sample of 100 texts
total_tokens = 0 # Keep track of total number of tokens

# Loop through each text, open XML file and parse dedication with epnames.py isname() function
# Highlight resulting text for review

for t in text_sample:
    input('Continue?')
    print(t)
    tree = etree.parse(f"/home/data/eebotcp/texts/{t[:3]}/{t}.xml", parser)
    xml = tree.getroot()
    dedications = xml.findall(".//tei:*[@type='dedication']", namespaces=nsmap)
    for d in dedications:
        tokens = d.xpath(".//tei:w|.//tei:pc", namespaces=nsmap)
        highlighted = []
        for t in tokens:
            ancestors = [ancestor.tag.split("}")[-1] for ancestor in t.iterancestors()]
            if t.text is not None and "note" not in ancestors and "bibl" not in ancestors:
                word = t.get("reg", t.text)
                if is_name(t):
                    highlighted.append(f"{Fore.GREEN}{word}{Style.RESET_ALL}")
                else:
                    highlighted.append(word)
        ded_text = " ".join(highlighted)
        print(ded_text)
        total_tokens += len(highlighted)
        print("Number of tokens:", len(highlighted))
        print("Total so far:", total_tokens)
        print()
