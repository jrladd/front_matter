#! /usr/bin/env python3

import csv, glob, re, sqlite3, json, pycorpora, editdistance
from itertools import groupby, product
from operator import itemgetter
from collections import Counter
import networkx as nx
from networkx.algorithms import bipartite
from networkx.readwrite import json_graph

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
    clean_text = re.sub(r"^S\.|\bSaint\b", saintrepl, clean_text) #Normalize Saint abbreviations
    clean_text = clean_text.strip()
    abbreviations = {"K.":"King", "Tho.": "Thomas", "Apostle": "St.", "Monarch": "King"}
    for abbr, expand in abbreviations.items():
        clean_text = clean_text.replace(abbr, expand)
    return clean_text

def saintrepl(matchobj):
    """
    Function to deal with various saint abbreviations.
    """
    if matchobj.group(0) == 'S.':
        if len(matchobj.string.split()) <= 2:
            return "St."
    else:
        return "St."

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

def retrieve_names(ma_outputs):
    """
    Given a list of MorphAdorner output files, return all the
    multi-word proper nouns in a dictionary that keeps track of
    what *kind* of file (head, signed, body) the noun appeared in.
    """
    stoplist = ["God", "Gods", "India", "Britain", "Britains", "Britaine", "Brittain", "Brittaine", "England", "Englands", "London", "Londons", "Westminster", "Christian", "Christs", "Puritan", "Erastian", "Arminian", "Jerusalem"]
    all_names = {}
    for c in csvfiles:
        filename = c.split('/')[-1]
        filekey = filename.split('_')[0]
        filetype = filename.split('_')[-1].split('.')[0]
        # print(filekey, filetype)
        if filekey not in all_names:
            all_names[filekey] = {}
        if filetype not in all_names[filekey]:
            all_names[filekey][filetype] = []
        with open(c, 'r') as csvfile:
            reader = csv.reader(csvfile, delimiter='\t')
            reader = [r for r in reader]
            for k,g in groupby(reader, key=itemgetter(2)): # Change key function to deal with all np's?
                group = [x for x in g]
                if 'np' in k:
                    if len(group) == 1 and '.' not in group[0][0] and clean(group[0][0].title()) not in stoplist and (k != 'npg1' and k != 'npg2'):# and len(group) > 1:
                        # name = ' '.join([x[0] for x in group])
                        index = reader.index(group[0])
                        name = get_fullname(index, reader)
                        if name != None:
                            clean_name = clean(name)
                            # print(clean_name)
                            all_names[filekey][filetype].append(clean_name)
                    elif len(group) > 1:
                        first_index = reader.index(group[0])
                        last_index = reader.index(group[0])+len(group)
                        name = ' '.join([x[3] for x in group])
                        clean_name = clean(name)
                        if clean_name == 'Christ Jesus': #Special rule to deal with this common name variation
                            all_names[filekey][filetype].append('Jesus Christ')
                        else:
                            name = get_title(clean_name, reader, first_index, last_index)
                            clean_name = clean(name)
                            all_names[filekey][filetype].append(clean_name)
    return all_names

def get_fullname(name_index, reader):
    """
    Given a name index and a list of morphadorner outputs, return a full name token
    from the words around it.
    """
    prefixes = pycorpora.humans.prefixes["prefixes"]
    prefixes.extend(["Mris", "Mris.", "Sr", "Sr.", "Prophet", "Honorable", "Honourable", "Master", "Alderman", "Servant", "Worshipful", "Worthy", "Noble", "Cap.", "Captain"])
    stopwords = pycorpora.words.stopwords.en["stopWords"]
    try:
        if clean(reader[name_index-1][0].title()) not in prefixes and clean(reader[name_index-1][0].lower()) not in stopwords:
            before = reader[name_index-1][0]
        else:
            before = None
    except IndexError:
        before = None
    try:
        if reader[name_index+1][0].lower() not in stopwords:
            after = reader[name_index+1][0]
        else:
            after = None
    except IndexError:
        after = None
    if before and (before.istitle() or before.isupper()):
        if after and (after.istitle() or after.isupper()):
            name = ' '.join([r[3] for r in reader[name_index-1:name_index+2]])
            name = get_title(name, reader, name_index-1, name_index+2)
        else:
            name = ' '.join([r[3] for r in reader[name_index-1:name_index+1]])
            name = get_title(name, reader, name_index-1, name_index+1)
    elif after and (after.istitle() or after.isupper()):
        name = ' '.join([r[3] for r in reader[name_index:name_index+2]])
        name = get_title(name, reader, name_index, name_index+2)
    else:
        name = None

    return name

def get_title(name, reader, first_index, last_index):
    # "Earle", "Lady", "Viscount"
    if re.search(r"Lord$|Earl$|Earle$|Duke$|Lady$|Viscount$|Archbishop$", name):
    # if name.endswith("Lord") or name.endswith("Earl") or name.endswith("Duke"):
        if reader[last_index][3].lower() == "of":
            name = ' '.join([r[3] for r in reader[first_index:last_index+2]])
        else:
            name = ' '.join([r[3] for r in reader[first_index:last_index+1]])
    return name

def create_edgelist(csvfiles):
    """
    Given a list of MorphAdorner output files, detect all names,
    count them, and put them into a manageable edgelist form.
    """
    all_names = retrieve_names(csvfiles)
    all_names = standardize(all_names)
    print(all_names)
    all_names_counted = {k:{x:Counter(y) for x,y in v.items()} for k,v in all_names.items()}
    edgelist = []
    for source,v in all_names_counted.items():
        for type,y in v.items():
            for target,weight in y.items():
                edgelist.append((source,target,{'type':type,'weight':weight}))
    return edgelist

def standardize(all_names):
    """
    Given a dictionary of discovered names, standardize names into unique lists.
    """
    all_names_list = []
    standards_list = []
    for k,v in all_names.items():
        for type,l in v.items():
            all_names_list.extend(l)
    unique_names_list = list(set(all_names_list))
    # print(unique_names_list)
    for x in product(unique_names_list, repeat=2):
        if len(x[0]) > 5 and len(x[1]) > 5:
            if len(x[0].split()) > 2 or len(x[1].split()) > 2:
                wd = editdistance.eval(x[0].split(), x[1].split())
                if wd == 1:
                    ld = editdistance.eval(x[0].split()[-1], x[1].split()[-1])
                    if ld <= 2 and (x[0].split()[-1] != x[1].split()[-2] or x[1].split()[-1] != x[0].split()[-2]):
                        print(x[0], x[1])
                        add_to_standards(x, standards_list)
                        
            else:
                ed = editdistance.eval(x[0],x[1])
                if 0 < ed < 3 and x[0][0] == x[1][0]:
                    surname1 = x[0].split()[-1]
                    surname2 = x[1].split()[-1]
                    sd = editdistance.eval(surname1, surname2)
                    if sd != 2:
                        print(x[0], x[1])
                        add_to_standards(x, standards_list)
    new_all_names = {}
    for k,v in all_names.items():
        new_all_names[k] = {} 
        for text_type, names in v.items():
            new_all_names[k][text_type] = []
            for name in names:
                if all(name not in namelist for namelist in standards_list) and name != '':
                    new_all_names[k][text_type].append(name)
                else:
                    for namelist in standards_list:
                        if name in namelist:
                            new_all_names[k][text_type].append(str(namelist))
    return new_all_names
        

def add_to_standards(x, standards_list):
    """Rules for adding uniques to standards_list"""
    if all(x[0] not in s for s in standards_list) and all(x[1] not in s for s in standards_list):
        standards_list.append([x[0], x[1]])
    else: 
        for s in standards_list:
            if x[0] in s and x[1] not in s:
                s.append(x[1])
            elif x[1] in s and x[0] not in s:
                s.append(x[0])

def create_graph(edgelist):
    """
    Given edgelist of texts/names, create NetworkX graph object.
    """
    B = nx.Graph()
    texts = list(set([e[0] for e in edgelist]))
    people = list(set([e[1] for e in edgelist]))
    B.add_nodes_from(texts, bipartite=0)
    B.add_nodes_from(people, bipartite=1)
    B.add_edges_from(edgelist)
    return B

def get_rank(dictionary, text_nodes):
    """
    Given dictionary of centrality attributes, return dictionary of rankings.
    """
    dictionary0 = {k:v for k,v in dictionary.items() if k in text_nodes}
    dictionary1 = {k:v for k,v in dictionary.items() if k not in text_nodes}
    sorted_dict0 = sorted(dictionary0.items(), key=itemgetter(1), reverse=True)
    sorted_dict1 = sorted(dictionary1.items(), key=itemgetter(1), reverse=True)
    print(sorted_dict1[:10])
    rank0 = {s[0]:sorted_dict0.index(s)+1 for s in sorted_dict0}
    rank1 = {s[0]:sorted_dict1.index(s)+1 for s in sorted_dict1}
    return dict(list(rank0.items())+list(rank1.items()))

def add_attributes_to_graph(B):
    """
    Add appropriate attributes to graph created from edgelist.
    """
    text_nodes = set(n for n,d in B.nodes(data=True) if d['bipartite'] == 0)
    deg_people,deg_texts=bipartite.degrees(B,text_nodes,'weight')
    betw=bipartite.betweenness_centrality(B,text_nodes)
    close=bipartite.closeness_centrality(B,text_nodes,normalized=True)

    degree_rank = get_rank(dict(list(dict(deg_people).items())+list(dict(deg_texts).items())), text_nodes)
    betw_rank = get_rank(betw, text_nodes)
    close_rank = get_rank(close, text_nodes)

    # Get metadata from EEBO_TCP
    conn = sqlite3.connect("data/eebo_tcp_metadata.sqlite")
    c = conn.cursor()
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
    # components = nx.connected_components(B)
    # largest_component = max(components, key=len)
    # SB = B.subgraph(largest_component)
    # SB.remove_nodes_from(node for node, degree in deg_people.items() if degree <= 1)

    # Add all attributes
    nx.set_node_attributes(B, dict(list(dict(deg_people).items())+list(dict(deg_texts).items())), 'degree')
    nx.set_node_attributes(B, betw, 'betweenness')
    nx.set_node_attributes(B, close, 'closeness')
    nx.set_node_attributes(B, degree_rank, 'deg_rank')
    nx.set_node_attributes(B, betw_rank, 'betw_rank')
    nx.set_node_attributes(B, close_rank, 'close_rank')
    nx.set_node_attributes(B, title, 'title')
    nx.set_node_attributes(B, author, 'author')
    nx.set_node_attributes(B, date, 'date')


def write_json(B, filename):
    """
    Given NetworkX graph object and filename, create JSON representation for D3.
    """
    new_data = json_graph.node_link_data(B)
    with open('viz/'+filename, 'w') as output:
        json.dump(new_data, output, sort_keys=True, indent=4, separators=(',',':'))

if __name__ == "__main__":
    csvfiles = glob.glob('data/ma_split_outputs/*')

    edgelist = create_edgelist(csvfiles)
    # print(edgelist)
    print(len(edgelist))

    B = create_graph(edgelist)
    add_attributes_to_graph(B)
    write_json(B, '1640s_ma.json')
