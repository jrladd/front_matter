#! /usr/bin/env python3

import csv, json, sqlite3
from collections import Counter
from operator import itemgetter
import networkx as nx
from networkx.algorithms import bipartite

conn = sqlite3.connect("data/eebo_tcp_metadata.sqlite")

c = conn.cursor()

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
betw=bipartite.betweenness_centrality(B,text_nodes)
close=bipartite.closeness_centrality(B,text_nodes,normalized=True)

def get_rank(dictionary):
    dictionary0 = {k:v for k,v in dictionary.items() if k in text_nodes}
    dictionary1 = {k:v for k,v in dictionary.items() if k not in text_nodes}
    sorted_dict0 = sorted(dictionary0.items(), key=itemgetter(1), reverse=True)
    sorted_dict1 = sorted(dictionary1.items(), key=itemgetter(1), reverse=True)
    print(sorted_dict1[:10])
    rank0 = {s[0]:sorted_dict0.index(s)+1 for s in sorted_dict0}
    rank1 = {s[0]:sorted_dict1.index(s)+1 for s in sorted_dict1}
    return dict(list(rank0.items())+list(rank1.items()))

degree_rank = get_rank(dict(list(deg_people.items())+list(deg_texts.items())))
betw_rank = get_rank(betw)
close_rank = get_rank(close)
components = nx.connected_components(B)
largest_component = max(components, key=len)

title = {}
author = {}
date = {}
for n in B.nodes():
    if n in text_nodes:
        t = (n,)
        c.execute("SELECT title,author,date FROM metadata WHERE key = ?;", t)
        result = c.fetchone()
        if len(result[0]) > 50:
            title[n] = result[0][:50]+'...'
        else:
            title[n] = result[0]
        author[n] = result[1]
        date[n] = int(result[2])
    else:
        title[n] = None
        author[n] = None
        date[n] = None

# Create a "subgraph" of just the largest component
# Then calculate the diameter of the subgraph, just like you did with density.
# 

SB = B.subgraph(largest_component)
SB.remove_nodes_from(node for node, degree in deg_people.items() if degree <= 1)
nx.set_node_attributes(B, 'degree', dict(list(deg_people.items())+list(deg_texts.items())))
nx.set_node_attributes(B, 'betweenness', betw)
nx.set_node_attributes(B, 'closeness', close)
nx.set_node_attributes(B, 'deg_rank', degree_rank)
nx.set_node_attributes(B, 'betw_rank', betw_rank)
nx.set_node_attributes(B, 'close_rank', close_rank)
nx.set_node_attributes(B, 'title', title)
nx.set_node_attributes(B, 'author', author)
nx.set_node_attributes(B, 'date', date)
#SB.remove_node('Jesus Christ')

# Create a dictionary for the JSON needed by D3.
new_data = dict(
    nodes=[dict(
        id=n,
        degree=SB.node[n]['degree'],
        betweenness=SB.node[n]['betweenness'],
        closeness=SB.node[n]['closeness'],
        deg_rank=SB.node[n]['deg_rank'],
        betw_rank=SB.node[n]['betw_rank'],
        close_rank=SB.node[n]['close_rank'],
        title=SB.node[n]['title'],
        author=SB.node[n]['author'],
        date=SB.node[n]['date'],
        bipartite=SB.node[n]['bipartite']) for n in SB.nodes()],
    links=[dict(source=e[0], target=e[1], weight=e[2]) for e in SB.edges(data='weight')])

# Output json of the graph.
with open('viz/1640s_dedications.json', 'w') as output:
    json.dump(new_data, output, sort_keys=True, indent=4, separators=(',',':'))
