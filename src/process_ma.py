#! /usr/bin/env python3

import csv, glob, re, sqlite3, json, pycorpora, editdistance, ast
from itertools import groupby, product
from operator import itemgetter
from collections import Counter, defaultdict
import networkx as nx
from networkx.algorithms import bipartite
from networkx.readwrite import json_graph
from fuzzywuzzy import fuzz, process

title_regex = re.compile(r"\b(Lord|Earl|Duke|Lad(y|ie)|Vis?counte?|Archbishop|Bishop|Countess|Q(u|v)een|Sir|Ma(i|y)or|St\.?|King)e?\s(of)?\s?")

def clean(text):
    """
    Clean EM texts using basic regex functions. Handles uppercase words,
    long s, v to u, and vv to w.
    """
    clean_text = text.replace('\u017f', 's')
    clean_text = re.sub(r"\bI(?=[AEIOUaeiou])", "J", clean_text)
    clean_text = re.sub(r"\sEsq$|\sEsq.$|\sKt$|\sKt.$", "", clean_text)
    # clean_text = re.sub(r"\n", " ", clean_text)
    clean_text = re.sub(r"VV|Vv|UU|Uu", "W", clean_text)
    clean_text = re.sub(r'vv|uu', 'w', clean_text)
    clean_text = re.sub(r"(v|V)(?![AEIOUaeiou])", replV, clean_text)
    clean_text = re.sub(r"\b[A-Z]+\b", titlerepl, clean_text)
    clean_text = re.sub(r"^S\.|\bSaint\b", saintrepl, clean_text) #Normalize Saint abbreviations
    clean_text = clean_text.strip()
    abbreviations = {"K.":"King", "Tho.": "Thomas", "Ro.":"Robert", "Apostle": "St.", "Monarch": "King", "Q.":"Queen"}
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
    jesus_var = ["Christ", "Jesu", "Chryst"]
    all_names = {}
    for c in csvfiles:
        filename = c.split('/')[-1]
        print("Processing:",filename)
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
                            if any(j in clean_name for j in jesus_var): #Special rule to deal with this common name variation
                                all_names[filekey][filetype].append('Jesus Christ')
                            else:
                                # print(clean_name)
                                all_names[filekey][filetype].append(clean_name)
                    elif 1 < len(group) < 5 and re.match(r"^[A-Z]\.\s?[A-Z]\.$",' '.join([x[3] for x in group])) == None: #Filter out just initials and long multi-name strings
                        first_index = reader.index(group[0])
                        last_index = reader.index(group[0])+len(group)
                        name_tokens = [x[3] for x in group]
                        name = ' '.join(name_tokens)
                        clean_name = clean(name)
                        if any(j in clean_name for j in jesus_var): #Special rule to deal with this common name variation
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
        if clean(reader[name_index-1][0]) != "" and clean(reader[name_index-1][0].title()) not in prefixes and clean(reader[name_index-1][0].lower()) not in stopwords:
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
            name = clean(name)
            name = get_title(name, reader, name_index-1, name_index+2)
        else:
            name = ' '.join([r[3] for r in reader[name_index-1:name_index+1]])
            name = clean(name)
            name = get_title(name, reader, name_index-1, name_index+1)
    elif after and (after.istitle() or after.isupper()):
        name = ' '.join([r[3] for r in reader[name_index:name_index+2]])
        name = clean(name)
        name = get_title(name, reader, name_index, name_index+2)
    else:
        name = None

    return name

def get_title(name, reader, first_index, last_index):
    # "Earle", "Lady", "Viscount"
    if re.search(r"(Lord|Earl|Duke|Lad(y|ie)|Vis?counte?|Archbishop|Bishop|Countess|Q(u|v)een|Sir|Ma(i|y)or)e?$", name):
    # if name.endswith("Lord") or name.endswith("Earl") or name.endswith("Duke"):
        try:
            if reader[last_index][3].lower() == "of":
                name = ' '.join([r[3] for r in reader[first_index:last_index+2]])
            else:
                name = ' '.join([r[3] for r in reader[first_index:last_index+1]])
        except IndexError:
            name = ' '.join([r[3] for r in reader[first_index:last_index+1]])
    return name

def create_edgelist(csvfiles):
    """
    Given a list of MorphAdorner output files, detect all names,
    count them, and put them into a manageable edgelist form: a list of
    tuples with nameId, textId, type, weight, and name variants
    """
    all_names = retrieve_names(csvfiles)
    standardized_full = standardize(all_names)
    name_by_id = {v:k for k,v in standardized_full.items()} # Will need standardized dictionary to be reversed
    edgetuples = []
    for textId,namelists_by_type in all_names.items(): # Iterate through dict
        for type,namelist in namelists_by_type.items(): # Subdict has info about type
            # Create standardized namelists of just the IDs for name groups
            # standardized_namelist = []
            for n in namelist:
                edgetuples.append((n,textId))
            #     try:
            #         standardized_namelist.append(standardized_full[n])
            #     except KeyError:
            #         for k in standardized_full.keys():
            #             if n in k:
            #                 standardized_namelist.append(standardized_full[k])
            #
            # # Count up the IDs to edge weights
            # counted = Counter(standardized_namelist)
            #
            # #Put it all together into a list of dictionaries
            # for c,weight in counted.items():
            #     edgelist.append({'nameId': c, 'textId': textId, 'type': type, 'weight': weight, 'name_variants': name_by_id[c]})
    standardized_edgetuples = []
    for name, textId in edgetuples:
        try:
            nameId = standardized_full[name]
        except KeyError:
            for k in standardized_full.keys():
                if "[" in k and name in ast.literal_eval(k):
                    nameId = standardized_full[k]
        standardized_edgetuples.append((nameId,textId))

    counted_edgetuples = Counter(standardized_edgetuples)
    edgelist = []
    for edgetuple, weight in counted_edgetuples.items():
        edgelist.append({'nameId': edgetuple[0], 'textId': edgetuple[1], 'weight': weight})

    return edgelist, name_by_id

def fuzzymatch(all_names):
    """
    Given a dictionary of discovered names, find standard names using fuzzy matching
    """
    standardized_full = {} # Our final goal, each name group with unique ID
    standards_list = []
    title = re.compile(r"\s(Lord|Earl|Earle|Duke|Lady|Viscount|Archbishop|Bishop|Countess|Countesse|D\.)\s")
    # Create a flat list of all names
    all_names_list = []
    for k,v in all_names.items():
        for type,l in v.items():
            all_names_list.extend(l)
    unique_names_list = list(set(all_names_list)) # Get just unique names for matching
    # print(unique_names_list)
    for u in unique_names_list:
        # Make sure the name isn't in list of possible matches
        choices = [c for c in unique_names_list if c != u]
        # Initial matching using sets of words
        match = process.extractOne(u, choices, scorer = fuzz.token_set_ratio)
        # print(u, match)
        if match[1] > 85: # Make match threshold fairly high
            # To deal with first name/last name issues, split up word and possible match
            # Run fuzzy matching on the word that disagrees
            word = u.split()
            possible_match = match[0].split()
            if len(word) == 2 and len(possible_match) == 2: # If both strings are two words
                print(u, match, "POSSIBLE") # Achieve possible match
                print("CONSIDERED", word, possible_match)
                if word[0] == possible_match[0]: # Same first name
                    match_lastname = fuzz.partial_ratio(word[1], possible_match[1])
                    print(match_lastname)
                    if match_lastname > 85:
                        print("MATCHED!")
                        add_to_standards((u, match[0]), standards_list)
                elif word[1] == possible_match[1]: # Same last name
                    match_firstname = fuzz.partial_ratio(word[0], possible_match[0])
                    print(match_firstname)
                    if match_firstname > 85:
                        print("MATCHED!")
                        add_to_standards((u, match[0]), standards_list)
            # Old code for matching with weird titles, but increasing the original match threshold solves this
                else:
                    add_to_standards((u, match[0]), standards_list)
            elif re.search(title, u) and re.search(title, match[0]):
                if fuzz.ratio(word[0], possible_match[0]) > 90 and fuzz.ratio(word[-1], possible_match[-1]) > 90:
                    print(u, match, "MATCHED!")
                    add_to_standards((u, match[0]), standards_list)
            else:
                # print(u, match, "MATCHED!")
                add_to_standards((u, match[0]), standards_list)
            print()

    # Assign unique IDs to every unique name, with only one ID for each matched group
    for i,u in enumerate(unique_names_list, start=1000001):
        if all(u not in namelist for namelist in standards_list) and u != '':
            standardized_full[u] = i
        else:
            for namelist in standards_list:
                if u in namelist:
                    standardized_full[str(namelist)] = i
    return standardized_full


    # print(all_names)
        # else:
            # print(u, match)
def match_name(name1, name2, title_regex):
    """
    Determine if two early modern names match one another.
    Combines fuzzy matching with special rules for titles.
    """
    threshold = 90 # Ratio threshold for fuzzy match
    if name1 != name2 and len(name1) > 5 and len(name2) > 5: # Basic character count threshold
        # Look for titles in both names
        match1 = re.search(title_regex, name1)
        match2 = re.search(title_regex, name2)
        if match1 and match2: # If both names have titles
            if fuzz.ratio(match1.group(0), match2.group(0)) >= threshold: # See if those titles are the same
                # Remove titles from name
                simplename1 = name1.replace(match1.group(0), '')
                simplename2 = name2.replace(match2.group(0), '')
                if fuzz.token_sort_ratio(simplename1, simplename2) >= threshold: # See if remaining name meets threshold
                    print(name1, name2, "MATCH!")
                    return True
        # Do the same if only one of the two names has a title in it
        elif match1:
            simplename1 = name1.replace(match1.group(0), '')
            if fuzz.token_sort_ratio(simplename1, name2) >= threshold:
                print(name1, name2, "MATCH!")
                return True
        elif match2:
            simplename2 = name2.replace(match2.group(0), '')
            if fuzz.token_sort_ratio(name1, simplename2) >= threshold:
                print(name1, name2, "MATCH!")
                return True
        # For all the rest of the names, see if they simply meet the threshold
        elif fuzz.token_sort_ratio(name1, name2) >= threshold:
            print(name1,name2, "MATCH!")
            return True

def standardize(all_names):
    """
    Given a dictionary of discovered names, standardize names into unique lists.
    This is no longer needed since adopting fuzzy matching, above.
    """
    all_names_list = []
    standards_list = []
    for k,v in all_names.items():
        for type,l in v.items():
            all_names_list.extend(l)
    unique_names_list = list(set(all_names_list))
    # print(unique_names_list)
    for names in product(unique_names_list, repeat=2):
        name1 = names[0]
        name2 = names[1]
        if match_name(name1, name2, title_regex):
            # print(name1,name2,"MATCH!")
            add_to_standards(names, standards_list)
        # namelist1 = name1.split()
        # namelist2 = name2.split()
        # if len(name1) > 5 and len(name2) > 5:
        #     if len(namelist1) > 2 or len(namelist2) > 2:
        #         wd = editdistance.eval(namelist1, namelist2)
        #         if wd == 1:
        #             ld = editdistance.eval(namelist1[-1], namelist2[-1])
        #             if ld <= 2 and (namelist1[-1] != namelist2[-2] or namelist1[-1] != namelist2[-2]):
        #                 print(name1, name2)
        #                 add_to_standards(names, standards_list)
        #
        #     else:
        #         ed = editdistance.eval(name1,name2)
        #         if 0 < ed < 3 and name1[0] == name2[0]:
        #             surname1 = namelist1[-1]
        #             surname2 = namelist2[-1]
        #             sd = editdistance.eval(surname1, surname2)
        #             if sd < 2:
        #                 print(name1,name2)
        #                 add_to_standards(names, standards_list)

    standardized_full = {}
    for i,u in enumerate(unique_names_list, start=1000001):
        if all(u not in namelist for namelist in standards_list) and u != '':
            standardized_full[u] = i
        else:
            for namelist in standards_list:
                if u in namelist:
                    standardized_full[str(namelist)] = i
    return standardized_full


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
    print("Creating graph object...")
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

def filter_one_degree(B):
    # tokenized_names = [a.split() for a in all_people if "[" not in a]
    # tokenized_names = sum(tokenized_names, [])
    # common_names = [k for k,v in Counter(tokenized_names).items() if v > 1]
    # print(common_names)
    # for p in one_degree_people:
    #     if all(n not in common_names for n in p.split()):
    #         print(p)
    node_subset = [n for n in B.nodes() if n != '1033538']
    subgraph = nx.subgraph(B, node_subset)
    return subgraph


def add_attributes_to_graph(B, name_by_id):
    """
    Add appropriate attributes to graph created from edgelist.
    """
    # B = filter_one_degree(B)
    print("Calculating Bipartite Centralities...")
    text_nodes = set(n for n,d in B.nodes(data=True) if d['bipartite'] == 0)
    people_nodes = set(B) - text_nodes
    print("Degree...")
    deg_people,deg_texts=bipartite.degrees(B,text_nodes,'weight')
    # one_degree_people = [k for k,v in dict(deg_people).items() if v == 1]
    # print("(Filter out one-degree nodes...)")
    # B = filter_one_degree(one_degree_people, B)
    # print("Betweenness...")
    # betw=bipartite.betweenness_centrality(B,text_nodes)
    # print("Closeness...")
    # close=bipartite.closeness_centrality(B,text_nodes,normalized=True)

    print("Ranking nodes by degree...")
    degree_rank = get_rank(dict(list(dict(deg_people).items())+list(dict(deg_texts).items())), text_nodes)
    # betw_rank = get_rank(betw, text_nodes)
    # close_rank = get_rank(close, text_nodes)

    print("Getting metadata for all nodes...")
    # Get metadata from EEBO_TCP
    conn = sqlite3.connect("data/eebo_tcp_metadata.sqlite")
    c = conn.cursor()
    title = {}
    author = {}
    date = {}
    name_variants = {}
    for n in B.nodes():
        if n in text_nodes:
            print("Adding text", n)
            t = (n,)
            c.execute("SELECT title,author,date FROM metadata WHERE key = ?;", t)
            result = c.fetchone()
            if result != None:
                if len(result[0]) > 50:
                    title[n] = result[0][:50]+'...'
                else:
                    title[n] = result[0]
                author[n] = result[1]
                if result[2] != None:
                    date[n] = int(result[2])
                else:
                    date[n] = result[2]
            name_variants[n] = None
        else:
            title[n] = None
            author[n] = None
            date[n] = None
            name_variants[n] = name_by_id[int(n)]

    # Create a "subgraph" of just the largest component
    # Then calculate the diameter of the subgraph, just like you did with density.
    # components = nx.connected_components(B)
    # largest_component = max(components, key=len)
    # SB = B.subgraph(largest_component)
    # SB.remove_nodes_from(node for node, degree in deg_people.items() if degree <= 1)
    print("Adding all node attributes...")
    degree = dict(list(dict(deg_people).items())+list(dict(deg_texts).items()))
    # Add all attributes
    nx.set_node_attributes(B, degree , 'degree')
    # nx.set_node_attributes(B, betw, 'betweenness')
    # nx.set_node_attributes(B, close, 'closeness')
    nx.set_node_attributes(B, degree_rank, 'deg_rank')
    # nx.set_node_attributes(B, betw_rank, 'betw_rank')
    # nx.set_node_attributes(B, close_rank, 'close_rank')
    nx.set_node_attributes(B, title, 'title')
    nx.set_node_attributes(B, author, 'author')
    nx.set_node_attributes(B, date, 'date')
    nx.set_node_attributes(B, name_variants, 'name_variants')


def write_json(B, filename):
    """
    Given NetworkX graph object and filename, create JSON representation for D3.
    """
    print("Writing JSON file...")
    new_data = json_graph.node_link_data(B)
    with open('viz/'+filename, 'w') as output:
        json.dump(new_data, output, sort_keys=True, indent=4, separators=(',',':'))

if __name__ == "__main__":
    # First stage: "NER" files and create edgelist
    csvfiles = glob.glob('data/ma_outputs_all/*')
    # csvfiles = csvfiles[500:1000]
    edgelist, name_by_id = create_edgelist(csvfiles)
    # print(edgelist)
    # print(len(edgelist))
    # edges = [e for e in edgelist]
    #
    with open('data/all_edgelist.csv', 'w') as newcsv:
       fieldnames = list(edgelist[0].keys())
       writer = csv.DictWriter(newcsv, delimiter="|",fieldnames=fieldnames)
       writer.writeheader()
       writer.writerows(edgelist)

    # Second stage: Read edgelist file in from CSV and build graph
    # with open('data/all_edgelist.csv', 'r') as edgecsv:
    #     reader = csv.DictReader(edgecsv, delimiter="|")
    #     edgelist = [(r['textId'], str(r['nameId']), {'weight':int(r['weight']), 'name_variants':r['name_variants']}) for r in reader]

    # print(edgelist)
    edgelist = [[edge['textId'],str(edge['nameId']), {'weight': edge['weight']}] for edge in edgelist]
    print(edgelist)

    B = create_graph(edgelist)
    add_attributes_to_graph(B, name_by_id)
    write_json(B, 'all_eebo.json')
