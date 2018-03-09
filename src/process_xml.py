#! /usr/bin/env python3.6

from bs4 import BeautifulSoup
import glob, re, spacy
from spacy import displacy

def check_tags(dedication):
    # print(dedication)
    clean_text = preprocess(dedication.text)
    doc = nlp(clean_text)
    displacy.serve(doc,style='ent',options={'ents':['PERSON']})
    author = dedication.select('signed')
    for a in author:
        print("Text:", a.text)
        ner(a.text)
        a.extract()
    dedicatee = dedication.select('head')
    for d in dedicatee:
        print("Text:", d.text)
        ner(d.text)
        d.extract()
    print("Other names:")
    ner(dedication.text)

def preprocess(text):
    clean_text = text.replace('\u017f', 's')
    clean_text = re.sub(r"\bI(?=[AEIOUaeiou])", "J", clean_text)
    clean_text = re.sub(r"VV|Vv", "W", clean_text)
    clean_text = clean_text.replace('vv', 'w')
    clean_text = re.sub(r"\b[A-Z]+\b", titlerepl, clean_text)
    return clean_text

def titlerepl(matchobj):
    return matchobj.group(0).title()

def ner(text):
    clean_text = preprocess(text)
    doc = nlp(clean_text)
    for ent in doc.ents:
        if ent.label_ == "PERSON" and " " in ent.orth_:
            print("Name:", ent.orth_)

nlp = spacy.load('en', parser=False)
xmlfiles = glob.glob("data/1640s_xml/*.xml")

for x in xmlfiles[:25]:
    with open(x, "r") as xmlfile:
        soup = BeautifulSoup(xmlfile.read(), "xml")
        dedications = soup.select("[type='dedication']")
    if len(dedications) > 0:
        for d in dedications:
            check_tags(d)
        # for i,d in enumerate(dedications):
        #     with open("data/1640s_txt/"+x[15:-4]+"-"+str(i)+".txt", "w") as txtfile:
        #         txtfile.write(d.text)
        #     print("Wrote file for ", x[15:-4])
    else:
        print("No dedication found")
    print()
