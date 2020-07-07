#! /usr/bin/env python3

from lxml import etree
import glob, csv, sys, pycorpora, re
from itertools import groupby

stopwords = pycorpora.geography.nationalities["nationalities"]
stopwords.extend(pycorpora.geography.countries["countries"])
stopwords.extend(pycorpora.geography.english_towns_cities["towns"])
stopwords.extend(pycorpora.geography.english_towns_cities["cities"])
stopwords.extend(["London", "Westminster", "England", "Scotland"])

prefixes = pycorpora.humans.prefixes["prefixes"]
prefixes.extend(["Mris", "Mris.", "Sr", "Sr.", "Prophet", "Master", "Alderman", "Cap.", "Captain", "Vicount", "Viscount", "Vicounte", "Viscounte", "Apostle", "Monarch", "K.", "Q.", "Saint", "St", "S.", "St.", "Mayor", "Mayore", "Maior", "Maiore"])

first_names = pycorpora.humans.firstNames["firstNames"]

def tag_iob(tag, sentence):
    if len(sentence) == 0:
        if is_proper_noun(tag) == True or is_personal_title(tag) == True:
            return "B-PERSON"
        else:
            return "O"
    elif sentence[-1][1] == "B-PERSON" or sentence[-1][1] == "I-PERSON":
        if is_proper_noun(tag) == True or is_personal_title(tag) == True or is_personal_of == True:
            return "I-PERSON"
        else:
            return "O"
    elif is_proper_noun(tag) == True or is_personal_title(tag) == True:
        return "B-PERSON"
    else:
        return "O"

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
        if tag.get('reg', tag.text) == "of" and (is_proper_noun(next_tag) == True or is_personal_title(next_tag) == True) and (is_proper_noun(previous_tag) == True or is_personal_title(previous_tag) == True):
            return True
        else:
            return False
    else:
        return False

def is_personal_comma(tag):
    if tag != None:
        next_tag = tag.getnext()
        previous_tag = tag.getprevious()
        if tag.text == "," and is_personal_title(next_tag) == True and is_proper_noun(previous_tag) == True:
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
    if tag.get('pos', '') == 'ab':
        return True
    else: 
        return False

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

def is_roman_numeral(tag):
    if tag.text != None and re.fullmatch(r"[IV]+", tag.get('reg', tag.text)):
        return True
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
    elif is_personal_title(tag) and (is_proper_noun(next_tag) or is_personal_of(next_tag) or is_personal_comma(previous_tag)):
        return True
    elif is_personal_of(tag):
        return True
    elif is_personal_comma(tag):
        return True
    elif is_abbrev(tag) and is_proper_noun(next_tag) and is_not_person(next_tag) == False:
        return True
    elif is_common_name(tag) and is_proper_noun(next_tag):
        return True
    elif upper_tag(tag) and upper_tag(previous_tag) and is_proper_noun(previous_tag) and is_not_person(previous_tag) == False:
        return True
    elif title_tag(tag) and title_tag(previous_tag) and is_proper_noun(previous_tag) and is_not_person(previous_tag) == False:
        return True
    elif is_roman_numeral(tag) and is_proper_noun(previous_tag):
        return True
    else:
        return False

if __name__ == "__main__":

    nsmap={'tei': 'http://www.tei-c.org/ns/1.0'}
    files = glob.glob("/home/data/eebotcp/texts/*/*.xml")
    parser = etree.XMLParser(collect_ids=False)
    print(pycorpora.humans.prefixes["prefixes"])
    for f in files:
        tree = etree.parse(f, parser)
        xml = tree.getroot()
        dedications = xml.findall(".//tei:*[@type='dedication']", namespaces=nsmap)
        for dedication in dedications:
            tokens = dedication.xpath(".//tei:w|.//tei:pc", namespaces=nsmap)
            tested = [(t.get('reg', t.text), is_name(t)) for t in tokens]
            for k,g in groupby(tested, key=lambda x:x[1]):
                if k == True:
                    print(" ".join([w for w,test in g]))
        #for w in xml.findall(".//tei:w", namespaces=nsmap):
                #print(w.get('reg', w.text), w.get('pos', ''))
        #xml = etree.XML(xmlfile.read().encode('utf8'))
#        all_sentences = get_iob_sentences(xml,nsmap)
#            with open('eebo_train.iob', 'a+') as trainingfile:
#                trainingfile.write('-DOCSTART- -X- O O\n\n')
#                for sentence in all_sentences[:int(len(all_sentences)/2)]:
#                    for token in sentence:
#                        trainingfile.write("{}\t{}\n".format(token[0], token[1]))
#                    trainingfile.write("\n")
#        with open('eebo_dev_0629.iob', 'a+') as trainingfile:
#            trainingfile.write('-DOCSTART- -X- O O\n\n')
#            for sentence in all_sentences:
#                for token in sentence:
#                    trainingfile.write("{}\t{}\n".format(token[0], token[1]))
#                trainingfile.write("\n")
#        print("Finished a file!", f)
