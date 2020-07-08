#! /usr/bin/env python3

from lxml import etree
import glob, csv, sys, pycorpora, re
from itertools import groupby
from collections import Counter

stopwords = pycorpora.geography.nationalities["nationalities"]
stopwords.extend(pycorpora.geography.countries["countries"])
stopwords.extend(pycorpora.geography.english_towns_cities["towns"])
stopwords.extend(pycorpora.geography.english_towns_cities["cities"])
stopwords.extend(["London", "Westminster", "England", "Scotland", "Thames", "Christian", "Christians", "Christian's", "Candlemas", "Christmas", "Jews", "Jew", "Israelites", "Egyptians", "Protestant", "Protestants", "Catholic", "Catholics", "Presbyterian", "Presbyterians", "Puritan", "Puritans", "Papist", "Papists", "Evangelical", "Version", "Hospital", "Surrey", "Barnstable", "Devon", "Wales", "Elysians", "Martyrs", "College", "Turks", "Canaanites", "Hampshire", "Huns", "Jesuits", "Enchiridion", "January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December", "Trinity"])

prefixes = pycorpora.humans.prefixes["prefixes"]
prefixes.extend(["Mris", "Mris.", "Sr", "Sr.", "Prophet", "Master", "Alderman", "Cap.", "Captain", "Vicount", "Viscount", "Vicounte", "Viscounte", "Apostle", "Monarch", "K.", "Q.", "Saint", "St", "S.", "St.", "Mayor", "Mayore", "Maior", "Maiore"])

first_names = pycorpora.humans.firstNames["firstNames"]
first_names.extend(["Will"])

ordinals = ["First", "Second", "Third", "Fourth", "Fifth", "Sixth", "Seventh", "Eighth", "Ninth", "Tenth"]

def is_proper_noun(tag):
    if tag != None and "nn" in tag.get('pos', '') and "j" not in tag.get('pos', ''):
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
        if tag.get('reg', tag.text) == "of" and (is_proper_noun(next_tag) or is_personal_title(next_tag) or upper_tag(next_tag) or title_tag(next_tag)) and (is_proper_noun(previous_tag) or is_personal_title(previous_tag)):
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
        if tag.text != None and (re.fullmatch(r"[IV]+\.?|[1-9](r?d\.?|th\.?)", tag.get('reg', tag.text)) or tag.get('reg', tag.text).title() in ordinals):
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

if __name__ == "__main__":

    nsmap={'tei': 'http://www.tei-c.org/ns/1.0'}
    files = glob.glob("/home/data/eebotcp/texts/*/*.xml")
    parser = etree.XMLParser(collect_ids=False)
    names = []
    for f in files[:200]:
        tree = etree.parse(f, parser)
        xml = tree.getroot()
        dedications = xml.findall(".//tei:*[@type='dedication']", namespaces=nsmap)
        for dedication in dedications:
            tokens = dedication.xpath(".//tei:w|.//tei:pc", namespaces=nsmap)
            tested = [(t.get('reg', t.text), is_name(t)) for t in tokens]
            for k,g in groupby(tested, key=lambda x:x[1]):
                if k == True:
                    name = " ".join([w for w,test in g])
                    print(name)
                    names.append(name)
    print(Counter(names))
            #print(" ".join([t[0] for t in tested if t[0] is not None]))
