#! /usr/bin/env python3

import csv, json
from collections import Counter
import networkx as nx
from networkx.algorithms import bipartite

i_to_j = ['Iohn', 'Iames']
with open("data/1640s_expanded_curated_openrefine.tsv", 'r') as csvfile:
    reader = csv.reader(csvfile, delimiter='\t')
    new_list = []
    for r in reader:
        if len(r) > 4 and r[-1] != '':
            r[3] = 'Robert Devereux'
            r[-1] = ''
        if 'Laud' in r[3]:
            r[3] = 'William Laud'
        r[3] = r[3].replace('Iohn', 'John')
        r[3] = r[3].replace('Iames', 'James')
        r[3] = r[3].replace('S. Aug.', 'St. Augustine')
        r[3] = r[3].replace('S. Augustine', 'St. Augustine')
        r[3] = r[3].replace('St Augustine Archbishop', 'St. Augustine')
        r[3] = r[3].replace('St ', 'St. ')
        r[3] = r[3].replace('Saint', 'St.')
        r[3] = r[3].replace('Viscount Hereford', 'Robert Devereux')

        new_list.append(r)

cleaned = [[l for l in n if l != ''] for n in new_list]

cleaned_tuples = [tuple(c) for c in cleaned]
counted = Counter(cleaned_tuples)

aggregated = []
for k,v in counted.items():
    k = list(k)
    if v > 1:
        #print(k, v)
        k[1] = v*int(k[1])
        #print(k, v)

    aggregated.append(k)

B = nx.Graph()
texts = [a[0] for a in aggregated if a[2] == 't']
people = [a[3] for a in aggregated if a[2] == 't']
weighted_edges = [(a[0], a[3], int(a[1])) for a in aggregated if a[2] == 't']
B.add_nodes_from(texts, bipartite=0)
B.add_nodes_from(people, bipartite=1)
B.add_weighted_edges_from(weighted_edges)

#print(nx.is_connected(B))
text_nodes = set(n for n,d in B.nodes(data=True) if d['bipartite'] == 0)
deg_people,deg_texts=bipartite.degrees(B,text_nodes,'weight')
components = nx.connected_components(B)
largest_component = max(components, key=len)

# Create a "subgraph" of just the largest component
# Then calculate the diameter of the subgraph, just like you did with density.
# 

SB = B.subgraph(largest_component)
SB.remove_nodes_from(node for node, degree in deg_people.items() if degree <= 1)
nx.set_node_attributes(B, 'degree', dict(list(deg_people.items())+list(deg_texts.items())))
#SB.remove_node('Jesus Christ')

# Create a dictionary for the JSON needed by D3.
new_data = dict(
    nodes=[dict(
        id=n,
        degree=SB.node[n]['degree'],
        bipartite=SB.node[n]['bipartite']) for n in SB.nodes()],
    links=[dict(source=e[0], target=e[1], weight=e[2]) for e in SB.edges(data='weight')])

# Output json of the graph.
with open('viz/1640s_dedications.json', 'w') as output:
    json.dump(new_data, output, sort_keys=True, indent=4, separators=(',',':'))
