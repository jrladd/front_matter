#! /usr/bin/env python3

from lxml import etree
import networkx as nx
import glob, csv, sys, pycorpora, re, json, time
from itertools import groupby
from collections import Counter
from metaphone import doublemetaphone

stopwords = pycorpora.geography.nationalities["nationalities"]
stopwords.extend(pycorpora.geography.countries["countries"])
stopwords.extend(pycorpora.geography.english_towns_cities["towns"])
stopwords.extend(pycorpora.geography.english_towns_cities["cities"])

with open("data/stopwords.json", "r") as stopfile:
    stopwords.extend(json.loads(stopfile.read()))

stopwords = [s.lower() for s in stopwords]

prefixes = pycorpora.humans.prefixes["prefixes"]
prefixes.extend(["M.", "Mris", "Mris.", "Sr", "Sr.", "Prophet", "Master", "Alderman", "Cap.", "Captain", "Vicount", "Viscount", "Vicounte", "Viscounte", "Apostle", "Monarch", "K.", "Q.", "Saint", "St", "S.", "St.", "Mayor", "Mayore", "Maior", "Maiore"])

first_names = pycorpora.humans.firstNames["firstNames"]
first_names.extend(["Will"])

ordinals = ["First", "Second", "Third", "Fourth", "Fifth", "Sixth", "Seventh", "Eighth", "Ninth", "Tenth", "Eleventh", "Twelfth", "Thirteenth", "Fourteenth", "Fifteenth"]
ofs = ["of", "de", "du"]

with open('data/name_abbrev.json') as abbrevfile:
    abbrev = json.loads(abbrevfile.read())

def is_proper_noun(tag):
    if tag != None and (tag.get('pos', '') == 'nn1' or tag.get('pos', '') == 'nng1'):
        return True
    else:
        return False

def is_personal_title(tag):
    if tag != None and tag.get('reg', tag.text) in prefixes:
        return True
    else:
        return False

def is_personal_of(tag):
    if tag != None:
        next_tag = tag.getnext()
        previous_tag = tag.getprevious()
        reg = tag.get('reg', tag.text)
        if reg != None and reg.lower() in ofs and (is_proper_noun(next_tag) or is_personal_title(next_tag) or upper_tag(next_tag) or title_tag(next_tag)) and (is_proper_noun(previous_tag) or is_personal_title(previous_tag)):
            return True
        else:
            return False
    else:
        return False

def is_personal_comma(tag):
    if tag != None:
        next_tag = tag.getnext()
        previous_tag = tag.getprevious()
        if tag.text == "," and is_personal_title(next_tag) and is_proper_noun(previous_tag):
            return True
        else:
            return False
    else:
        return False

def is_personal_period(tag):
    if tag != None:
        next_tag = tag.getnext()
        previous_tag = tag.getprevious()
        if tag.text == "." and is_proper_noun(next_tag) and (is_proper_noun(previous_tag) or is_common_name(previous_tag)):
            return True
        else:
            return False
    else:
        return False

def is_personal_the(tag):
    if tag != None:
        next_tag = tag.getnext()
        previous_tag = tag.getprevious()
        if tag.text == "the" and (is_proper_noun(next_tag) or is_royal_numeral(next_tag)) and (is_proper_noun(previous_tag) or is_common_name(previous_tag)):
            return True
        else:
            return False
    else:
        return False

def is_not_person(tag):
    if tag.get('reg', tag.text).lower() in stopwords:
        return True
    else:
        return False

def is_abbrev(tag):
    if tag.text != None:
        if tag.get('pos', '') == 'ab' or re.fullmatch(r"[A-Z][a-z]{0,4}\.", tag.get('reg',tag.text)) or re.fullmatch(r"[A-Z]{1,4}\.", tag.get('reg',tag.text)):
            return True
        else: 
            return False
    else:
        False

def is_common_name(tag):
    if tag != None:
        if tag.text != None and tag.get('reg', tag.text).title() in first_names:
            return True
        else:
            return False
    else:
        return False

def upper_tag(tag):
    if tag != None:
        if tag.text != None and tag.get('reg', tag.text).isupper():
            return True
        else:
            return False
    else:
        return False

def title_tag(tag):
    if tag != None:
        if tag.text != None and tag.get('reg', tag.text).istitle():
            return True
        else:
            return False
    else:
        return False

def is_royal_numeral(tag):
    if tag != None:
        if tag.text != None and (re.fullmatch(r"[IVX]+\.?|[1-9](r?d\.?|th\.?)", tag.get('reg', tag.text)) or tag.get('reg', tag.text).title() in ordinals):
            return True
        else:
            return False
    else:
        return False

def is_initial(tag):
    if tag != None:
        if tag.text != None and re.fullmatch(r"[A-Z]\.", tag.get('reg', tag.text)):
            return True
        else:
            return False
    else:
        return False

def is_name(tag):
    next_tag = tag.getnext()
    previous_tag = tag.getprevious()
    if is_proper_noun(tag):
        if is_not_person(tag) and is_personal_of(previous_tag) == False and is_personal_title(previous_tag) == False:
            return False
        else:
            return True
    elif is_personal_title(tag) and (is_common_name(next_tag) or is_proper_noun(next_tag) or is_personal_of(next_tag) or is_personal_title(next_tag)):
        return True
    elif is_personal_title(tag) and is_personal_comma(previous_tag) and is_proper_noun(next_tag):
        return True
    elif is_personal_of(tag):
        return True
    elif is_personal_comma(tag):
        return True
    elif is_personal_period(tag):
        return True
    elif is_personal_the(tag):
        return True
    elif is_abbrev(tag) and (is_proper_noun(next_tag) or is_personal_title(next_tag)) and is_not_person(next_tag) == False:
        return True
    elif is_common_name(tag) and (is_proper_noun(next_tag) or is_personal_period(next_tag)):
        return True
    elif upper_tag(tag) and ((upper_tag(previous_tag) and is_proper_noun(previous_tag)) or is_personal_of(previous_tag)) and is_not_person(previous_tag) == False:
        return True
    elif title_tag(tag) and is_not_person(tag) == False and ((title_tag(previous_tag) and is_proper_noun(previous_tag)) or is_personal_of(previous_tag)) and is_not_person(previous_tag) == False:
        return True
    elif is_royal_numeral(tag) and (is_proper_noun(previous_tag) or is_personal_the(previous_tag) or is_common_name(previous_tag)):
        return True
    elif is_initial(tag) and (is_initial(previous_tag) or is_initial(next_tag)):
        return True
    else:
        return False

def fingerprint(name):
    testname = name
    if re.search(r"\bjesu", testname.lower()) != None or re.search(r"\bchrist\b", testname.lower()) != None:
        return ("christ", "")
    else:
        testname = re.sub(r"\band\b|\bor\b", "", testname)
        for p in prefixes:
            patt = f"\\b{p.lower()}\\b"
            testname = re.sub(patt, "", testname.lower())
        for k,v in abbrev.items():
            patt = f"\\b{k.lower()}\.?\\b"
            testname = re.sub(patt, v.lower(), testname.lower())
        testname = re.sub(r"\bfl\b|\bof\b|\bd\.|\bb\.", "", testname)
        testname = re.sub(r"[\.\?,!;:\(\)\-\[\]]|'s", "", testname)
        testname = re.sub(r"\d+", "", testname)
        if " " in testname:
    #        namelist = [name.split()[0][0]]
    #        namelist.extend(name.split()[1:])
    #        name = "".join(sorted(namelist))
            testname = "".join(sorted(testname.split()))
        dm = doublemetaphone(testname)
        #no_vowels = re.sub(r"[aeiouy]", "", testname.lower())
#        return (dm[0], dm[1], no_vowels)
        if dm[1] == '' and re.search(r"[aiouy]$", testname.lower()) != None:
            return (dm[0], f"{dm[0]}{testname[-1].upper()}")
        elif dm[1] == '' and re.search(r"^b", testname.lower()) != None:
            return (dm[0], f"{testname[0].upper()}{dm[0][1:]}")
        else:
            return dm

def is_author(name, author):
    initials = ''.join([a[0] for a in author.split()])
    if fingerprint(name) == fingerprint(author):
        return True
    elif re.sub(r'\W+', '', name).lower() == re.sub(r'\W+', '', initials).lower():
        return True
    else:
        return False

def count_edges(orig_edges, list_g):
    for e in orig_edges:
        if e[1] in list_g:
            if (e[0],new_id) not in edges_counter:
                edges_counter[(e[0], new_id)] = {}
                edges_counter[(e[0], new_id)]['weight'] = 1
                edges_counter[(e[0], new_id)]['is_author'] = [e[2]['is_author']]
                edges_counter[(e[0], new_id)]['container'] = [e[2]['container']]
            else:
                edges_counter[(e[0], new_id)]['weight'] += 1
                edges_counter[(e[0], new_id)]['is_author'].append(e[2]['is_author'])
                edges_counter[(e[0], new_id)]['container'].append(e[2]['container'])

def get_parents(e):
    ancestors = [ancestor.tag.split("}")[-1] for ancestor in e.iterancestors()]
    if "signed" in ancestors:
        return "signed"
    elif "head" in ancestors:
        return "head"
    else:
        return "body"

if __name__ == "__main__":

    start = time.process_time()
    nsmap={'tei': 'http://www.tei-c.org/ns/1.0', 'ep': 'http://earlyprint.org/ns/1.0'}
    files = glob.glob("/home/data/eebotcp/texts/*/*.xml")
    parser = etree.XMLParser(collect_ids=False)
    names = []
    orig_edges = []
    nodes = []
    for f in files:
        fileid = f.split("/")[-1].split(".")[0]
        tree = etree.parse(f, parser)
        xml = tree.getroot()
        dedications = xml.findall(".//tei:*[@type='dedication']", namespaces=nsmap)
        author = xml.find(".//ep:author", namespaces=nsmap).text
        if len(dedications) > 0:
            nodes.append((fileid, {"author": author}))
        for dedication in dedications:
            tokens = dedication.xpath(".//tei:w|.//tei:pc", namespaces=nsmap)
            tested = [(t.get('reg', t.text), is_name(t), get_parents(t)) for t in tokens]
            for k,g in groupby(tested, key=lambda x:x[1]):
                g = list(g)
                if k == True:
                    name = " ".join([w for w,test,p in g])
                    if is_author(name, author):
                        orig_edges.append((fileid, name, {"is_author": "true", "container": g[0][2]}))
                    else:
                        orig_edges.append((fileid, name, {"is_author": "false", "container": g[0][2]}))
                    names.append(name)
    sorted_names = sorted(names, key=fingerprint)
    new_id = 100000
    edges_counter = {}
    for k,g in groupby(sorted_names, fingerprint):
        new_id += 1
        list_g = list(g)
        nodes.append((new_id, {"display_name": Counter(list_g).most_common(1)[0][0].title(), "name_list": list_g}))
        count_edges(orig_edges, list_g)

    #print(nodes)
    edges = []
    for k,v in edges_counter.items():
        v['is_author'] = list(set(v['is_author']))[0]
        v['container'] = list(set(v['container']))
        edges.append((k[0], k[1], v))
    #print(edges)

    G = nx.Graph()
    G.add_nodes_from(nodes)
    G.add_edges_from(edges)
    nx.write_gpickle(G, 'test.pkl')

    end = time.process_time()
    print(end-start)
