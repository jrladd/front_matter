#! /usr/bin/env python3

#########################################
# This script takes as its input the data produced by epnames.py, but
# only after that data has been hand-cleaned using OpenRefine, where
# a 'cleanedname' column is added that disambiguates names.

# After processing this data and adding metadata from the
# EarlyPrint metadata repository: https://github.com/earlyprint/epmetadata,
# the data is turned into a NetworkX graph object and exported for
# further analysis in the Jupyter notebook explore_network.ipynb.
#########################################
from lxml import etree
import networkx as nx
import csv, re, time
from itertools import groupby
from collections import Counter, defaultdict

def count_edges(reader):
"""
This function aggregates edges and keeps track of their weights.
It reconstitutes the 'isauthor' and 'container' values as lists.
"""
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
        if any(a == 'true' for a in v['isauthor']): # If any item in the isauthor list is true, then we want to record this person as a likely author of the text
            v['isauthor'] = 'true'
        else:
            v['isauthor'] = 'false'
        v['container'] = list(set(v['container']))
        edges.append((k[0].split("_")[0], k[1], v))
    return edges

if __name__ == "__main__":

    start = time.process_time()

    # Import data that has been cleaned in OpenRefine
    with open("data/openrefine_edgesjoined0826.tsv", "r") as edgefile:
        reader = csv.DictReader(edgefile, delimiter="\t")
        edges = count_edges(reader) # Run count_edges() function from above
                
    # Distinguist between people (names) and texts for different node sets
    people = set([e[1] for e in edges])
    texts = set([e[0] for e in edges])
    nodes = []
    node_dict = {}
    person_id = 100001 # Assign each name a unique ID number
    # Assign attributes for each name
    for p in people:
        nodes.append((person_id, {'display_name': p.title(), 'bipartite': 'person'}))
        node_dict[p] = person_id
        person_id += 1
    # Assign attributes for each text using epmetadata
    nsmap = {'tei': 'http://www.tei-c.org/ns/1.0'}
    for t in texts:
        try:
            tree = etree.parse(f'../earlyprint/epmetadata/sourcemeta/{t}_sourcemeta.xml')
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
    # Put edges in correct NetworkX tuple form, with new nodeIDs
    edges = [(e[0], node_dict[e[1]], e[2]) for e in edges]

    # Create NetworkX Graph object, and add nodes and edges
    G = nx.Graph()
    G.add_nodes_from(nodes)
    G.add_edges_from(edges)
    print(nx.info(G)) # Print graph info
    nx.write_gpickle(G, 'data/test_joined0826.pkl') # Export Graph object as pickle

    end = time.process_time()
    print(end-start) # Print how long the process took
