#! /usr/bin/env python3.6

from bs4 import BeautifulSoup
import glob, re, spacy
from spacy import displacy

def check_tags(dedication):
    """
    Given an xml dedication, run NER on relevant parts of the text,
    and return extracted and categorized names.
    """
    signee_names = []
    author = dedication.select('signed')
    for a in author:
        # print("Text:", a.text)
        signees = ner(a.text)
        signee_names.extend(signees)
        a.extract()
    dedicatee_names = []
    dedicatee = dedication.select('head')
    for d in dedicatee:
        # print("Text:", d.text)
        dedicatees = ner(d.text)
        dedicatee_names.extend(dedicatees)
        d.extract()
    # print("Other names:")
    other_names = ner(dedication.text)
    all_names = dict(
        signees = signee_names,
        dedicatees = dedicatee_names,
        others = other_names
    )
    return all_names

def preprocess(text):
    """
    Clean EM texts using basic regex functions. Handles uppercase words,
    long s, v to u, and vv to w.
    """
    clean_text = text.replace('\u017f', 's')
    clean_text = re.sub(r"\bI(?=[AEIOUaeiou])", "J", clean_text)
    clean_text = re.sub(r"VV|Vv|UU|Uu", "W", clean_text)
    clean_text = re.sub('vv|uu', 'w', clean_text)
    # clean_text = re.sub(r"(v|V)(?![AEIOUaeiou])", replV, clean_text)
    clean_text = re.sub(r"\b[A-Z]+\b", titlerepl, clean_text)
    return clean_text

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

def ner(text):
    """
    Runs NER using Spacy, returns list of any multi-word matches for a person
    """
    clean_text = preprocess(text)
    doc = nlp(clean_text)
    names = [ent.orth_.strip() for ent in doc.ents if ent.label_ == "PERSON" and " " in ent.orth_]
    return names

def display_names(text):
    """
    Takes any text and extracts persons for display in browser, via displacy.
    """
    clean_text = preprocess(text)
    doc = nlp(clean_text)
    displacy.serve(doc,style='ent',options={'ents':['PERSON']})

def extract_authors(soup):
    """
    Using soup object, get author names from XML metadata headers.
    """
    author = soup.select("author")
    authors = list(set(a.text for a in author))
    return authors

nlp = spacy.load('en', parser=False)
xmlfiles = glob.glob("data/1640s_xml/*.xml")

for x in xmlfiles:
    with open(x, "r") as xmlfile:
        soup = BeautifulSoup(xmlfile.read(), "xml")
        dedications = soup.select("[type='dedication']")
    if len(dedications) > 0:
        # authors = extract_authors(soup)
        # for a in authors:
        #     print("Author:", a)
        for d in dedications:
            all_names = check_tags(d)
            print(all_names)
        print()
