#! /usr/bin/env python3

from lxml import etree
import glob, csv, sys, pycorpora, re
from itertools import groupby
from collections import Counter
from metaphone import doublemetaphone

stopwords = pycorpora.geography.nationalities["nationalities"]
stopwords.extend(pycorpora.geography.countries["countries"])
stopwords.extend(pycorpora.geography.english_towns_cities["towns"])
stopwords.extend(pycorpora.geography.english_towns_cities["cities"])
stopwords.extend(["London", "Westminster", "England", "Scotland", "Thames", "Candlemas", "Christmas", "Jews", "Jew", "Israelites", "Egyptians", "Protestant", "Protestants", "Catholic", "Catholics", "Presbyterian", "Puritan", "Papist", "Evangelical", "Version", "Hospital", "Surrey", "Barnstable", "Devon", "Wales", "College", "Turk", "Canaanite", "Hampshire", "Huns", "Jesuit", "Enchiridion", "January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December", "Trinity", "Athens", "Anabaptist", "Philistine", "Christendom", "Odyssey", "Iliad", "Europe", "Christianity", "Christian", "Rome", "Britain"])

prefixes = pycorpora.humans.prefixes["prefixes"]
prefixes.extend(["M.", "Mris", "Mris.", "Sr", "Sr.", "Prophet", "Master", "Alderman", "Cap.", "Captain", "Vicount", "Viscount", "Vicounte", "Viscounte", "Apostle", "Monarch", "K.", "Q.", "Saint", "St", "S.", "St.", "Mayor", "Mayore", "Maior", "Maiore"])

first_names = pycorpora.humans.firstNames["firstNames"]
first_names.extend(["Will"])

ordinals = ["First", "Second", "Third", "Fourth", "Fifth", "Sixth", "Seventh", "Eighth", "Ninth", "Tenth", "Eleventh", "Twelfth", "Thirteenth", "Fourteenth", "Fifteenth"]
ofs = ["of", "de", "du"]

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
    if tag.get('reg', tag.text).title() in stopwords:
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
    #name = name.lower()
    for p in prefixes:
        patt = f"\\b{p.lower()}\\b"
        name = re.sub(patt, "", name.lower())
    name = re.sub(r"[\.\?,!;:\(\)]", "", name)
    if " " in name:
#        namelist = [name.split()[0][0]]
#        namelist.extend(name.split()[1:])
#        name = "".join(sorted(namelist))
        name = "".join(sorted(name.split()))
    dm = doublemetaphone(name)
    no_vowels = re.sub(r"[aeiouy]", "", name.lower())
    return (dm[0], dm[1], no_vowels)

if __name__ == "__main__":

    nsmap={'tei': 'http://www.tei-c.org/ns/1.0'}
    files = glob.glob("/home/data/eebotcp/texts/*/*.xml")
    parser = etree.XMLParser(collect_ids=False)
    names = []
#    pos = []
    for f in files[:1000]:
        tree = etree.parse(f, parser)
        xml = tree.getroot()
        dedications = xml.findall(".//tei:*[@type='dedication']", namespaces=nsmap)
        for dedication in dedications:
            tokens = dedication.xpath(".//tei:w|.//tei:pc", namespaces=nsmap)
#            pos.extend([(t.get('reg', t.text), t.get('pos', '')) for t in tokens if "nn" in t.get('pos', '')])
#    print(Counter(pos))
#    pos = sorted(pos, key = lambda x:x[1])
#    for k,g in groupby(pos, key = lambda x:x[1]):
#        list_g = list(g)
#        print(k, len(list_g), list_g)
            tested = [(t.get('reg', t.text), is_name(t)) for t in tokens]
            for k,g in groupby(tested, key=lambda x:x[1]):
                if k == True:
                    name = " ".join([w for w,test in g]).strip("'s")
                    print(name)
                    names.append(name)
    print(Counter(names))
    sorted_names = sorted(names, key=fingerprint)
    new_id = 100000
    for k,g in groupby(sorted_names, fingerprint):
        list_g = list(g)
        print(k, list_g, len(list_g))
            #print(" ".join([t[0] for t in tested if t[0] is not None]))
