#! /usr/bin/env python3

from lxml import etree
import networkx as nx
import csv, re, time
from itertools import groupby
from collections import Counter, defaultdict

def get_metadata(xml):
    author = xml.find(".//ep:author", namespaces=nsmap)
    title = xml.find(".//ep:title", namespaces=nsmap)
    date = xml.find(".//ep:publicationYear", namespaces=nsmap)
    if author is not None:
        author = author.text
    else:
        author = ""
    if title is not None:
        title = title.text
    else:
        title = ""
    if date is not None:
        date = date.text
    else:
        date = ""
    return author, title, date

def count_edges(reader):
    edges_counter = {}
    for r in reader:
        if not re.fullmatch(r".", r['cleanedname']):
            if (r['textid'],r['cleanedname']) not in edges_counter:
                edges_counter[(r['textid'],r['cleanedname'])] = {}
                edges_counter[(r['textid'],r['cleanedname'])]['weight'] = 1
                edges_counter[(r['textid'],r['cleanedname'])]['isauthor'] = [r['isauthor']]
                edges_counter[(r['textid'],r['cleanedname'])]['container'] = [r['container']]
            else:
                edges_counter[(r['textid'],r['cleanedname'])]['weight'] += 1
                edges_counter[(r['textid'],r['cleanedname'])]['isauthor'].append(r['isauthor'])
                edges_counter[(r['textid'],r['cleanedname'])]['container'].append(r['container'])
    edges = []
    for k,v in edges_counter.items():
        if any(a == 'true' for a in v['isauthor']):
            v['isauthor'] = 'true'
        else:
            v['isauthor'] = 'false'
        v['container'] = list(set(v['container']))
        edges.append((k[0].split("_")[0], k[1], v))
    return edges

if __name__ == "__main__":

    start = time.process_time()
    #nsmap={'tei': 'http://www.tei-c.org/ns/1.0', 'ep': 'http://earlyprint.org/ns/1.0'}
    with open("openrefine_edges0818.tsv", "r") as edgefile:
        reader = csv.DictReader(edgefile, delimiter="\t")
        edges = count_edges(reader)
                
    people = set([e[1] for e in edges])
    texts = set([e[0] for e in edges])
    nodes = []
    person_id = 100001
    for p in people:
        nodes.append((person_id, {'display_name': p.title(), 'bipartite': 'person'}))
    nsmap = {'tei': 'http://www.tei-c.org/ns/1.0'}
    for t in texts:
        try:
            tree = etree.parse(f'../epmetadata/sourcemeta/{t}_sourcemeta.xml')
            xml = tree.getroot()
            author_el = xml.find(".//tei:author", namespaces=nsmap)
            if author_el != None:
                author = author_el.text
            else:
                author = 'No author listed'
            title = xml.find(".//tei:title", namespaces=nsmap).text
            date_el = xml.find(".//tei:date", namespaces=nsmap)
            if date_el != None:
                date = date_el.get("when", date_el.get("notBefore"))
            else:
                date = 'No date listed'
        except OSError:
            author = 'No author listed'
            title = 'No title listed'
            date = 'No date listed'
        nodes.append((t, {'author': author, 'title': title, 'date': date, 'bipartite': 'text'}))
    G = nx.Graph()
    G.add_nodes_from(nodes)
    G.add_edges_from(edges)
    print(nx.info(G))
    nx.write_gpickle(G, 'test0819.pkl')

    end = time.process_time()
    print(end-start)
