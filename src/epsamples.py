#! /usr/bin/env python3

from random import choice
import csv, re
from lxml import etree
from collections import Counter, defaultdict
from colorama import init, Fore, Back, Style
from epnames import is_name

with open('test_edges0811.csv', 'r') as csvfile:
    reader = csv.reader(csvfile, delimiter="\t")
    edges = [r for r in reader]

names_by_text = defaultdict(list)
for e in edges:
    names_by_text[e[0]].append(e[1])

names_by_text = {k:Counter(v) for k,v in names_by_text.items()}

textids = list(names_by_text.keys())

init()
nsmap={'tei': 'http://www.tei-c.org/ns/1.0', 'ep': 'http://earlyprint.org/ns/1.0'}
parser = etree.XMLParser(collect_ids=False)

x = 0
while x < 5:
    input('Continue?')
    random_id = choice(textids)
    print(random_id)
    for k,v in names_by_text[random_id].items():
        print(k, v)
    tree = etree.parse(f"/home/data/eebotcp/texts/{random_id[:3]}/{random_id}.xml", parser)
    xml = tree.getroot()
    dedications = xml.findall(".//tei:*[@type='dedication']", namespaces=nsmap)
    for d in dedications:
        tokens = d.xpath(".//tei:w|.//tei:pc", namespaces=nsmap)
        highlighted = []
        for t in tokens:
            if t.text is not None:
                word = t.get("reg", t.text)
                if is_name(t):
                    highlighted.append(f"{Fore.GREEN}{word}{Style.RESET_ALL}")
                else:
                    highlighted.append(word)
        #tokens = [t.get("reg", t.text).lower() for t in tokens if t.text is not None]
        ded_text = " ".join(highlighted)
        #ded_text = re.sub(r"\s+", " ", etree.tostring(d, method="text", encoding="UTF-8").decode('utf-8')).lower()
        #for k in names_by_text[random_id].keys():
        #    ded_text = re.sub(f"\\b{k}\\b", f"{Fore.GREEN}{k}{Style.RESET_ALL}", ded_text)
        print(ded_text)
        print()
    x += 1
