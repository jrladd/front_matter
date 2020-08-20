#! /usr/bin/env python3

# Begin by importing necessarly libraries
import networkx as nx
from networkx.readwrite import json_graph
from networkx.algorithms import bipartite, community
import json
import matplotlib
import matplotlib.pyplot as plt
import pandas as pd
import sqlite3
from pyvis.network import Network

def filter_by_year(year, B):
    """
    A function for creating subgraphs for each year
    """
    nodes = []
    for n in B.nodes(data=True):
        try:
            if int(n[1]['date']) == year:
                nodes.append(n[0])
                nodes.extend(B.neighbors(n[0]))
        except (KeyError, ValueError, TypeError) as e:
            pass
    SB = B.subgraph(nodes)
    return SB

def filter_by_range(start_year,end_year, B):
    """
    Similar to the year filter (above), filter the
    full graph by a range of years and create a subgraph.
    """
    nodes = []
    for n in B.nodes(data=True):
        try:
            if int(n[1]['date']) in range(start_year, end_year):
                nodes.append(n[0])
                nodes.extend(B.neighbors(n[0]))
        except (KeyError, ValueError, TypeError) as e:
            pass
    SB = B.subgraph(nodes)
    return SB

def convert_nx(nx_graph):
    """
    A function for creating visualizations based on NetworkX graphs.
    """
    viz = Network(width=800, height=800, notebook=True)
    viz.barnes_hut()
    edges = nx_graph.edges(data=True)
    nodes = nx_graph.nodes(data=True)
    for n in nodes:
        if n[1]['bipartite'] == 1:
            viz.add_node(n[0], label=n[1]['name_variants'], title=n[1]['name_variants'], shape='dot', color='orange', value=n[1]['degree'])
        elif n[1]['bipartite'] == 0:
            viz.add_node(n[0], label=n[1]['title'], title=n[1]['title'], shape='square', color='green', value=n[1]['degree'])
    for e in edges:
        viz.add_edge(e[0], e[1])

    viz.set_options("""{
      "nodes": {
        "scaling": {
          "min": 50,
          "max": 150
        }
      },
      "edges": {
        "color": {
          "inherit": true
        },
        "scaling": {
          "label": {
            "min": 500,
            "max": 1500,
            "maxVisible": 143,
            "drawThreshold": 0
          }
        },
        "smooth": false
      },
      "physics": {
        "barnesHut": {
          "gravitationalConstant": -80000,
          "springLength": 250,
          "springConstant": 0.001
        },
        "minVelocity": 0.75
      }
    }""")

    return viz

def create_dataframe(centralities, top_people, B):
    """
    A function to create a pandas dataframe of people's connections each year
    """
    people_counts_by_year = []
    for n in top_people:
        node_id = n
        centrality_dict = {}
        for year,centrality in centralities.items():
            if node_id in centrality:
                centrality_dict[year] = centrality[node_id]
            else:
                centrality_dict[year] = 0
        people_counts_by_year.append(centrality_dict)

    df = pd.DataFrame(people_counts_by_year, index=[B.node[t]['display_name'] for t in top_people])
    return df
