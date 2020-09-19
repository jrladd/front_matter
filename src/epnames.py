#! /usr/bin/env python3

"""
This is the main script for data collection. It takes a collection of
EarlyPrint XML documents as its input (those documents are partially public now at
earlyprint.org/download and will be fully public after the TCP Phase II release in
January 2021). 

After extracting dedications from the full XML document, it uses
EP's linguistic tagging to first determine if a word is a proper noun and then, using
the functions below, determine if the word is part of a name.

Names are then output as a TSV file for hand-curation in OpenRefine.
"""
from lxml import etree
import networkx as nx
import glob, csv, sys, pycorpora, re, json, time
from itertools import groupby
from collections import Counter
from metaphone import doublemetaphone

# Import stopwords of common place names and other proper nouns that
# are NOT personal names.

stopwords = pycorpora.geography.nationalities["nationalities"]
stopwords.extend(pycorpora.geography.countries["countries"])
stopwords.extend(pycorpora.geography.english_towns_cities["towns"])
stopwords.extend(pycorpora.geography.english_towns_cities["cities"])

with open("data/stopwords.json", "r") as stopfile:
    stopwords.extend(json.loads(stopfile.read()))

with open("data/stopwords0814.txt", "r") as stop2:
    stopwords.extend(stop2.read().split("\n")[:-1])

stopwords = [s.lower() for s in stopwords]

# Collect prefixes, ordinals, and common first names for later testing

prefixes = pycorpora.humans.prefixes["prefixes"]
prefixes.extend(["M.", "Mris", "Mris.", "Sr", "Sr.", "Prophet", "Master", "Alderman", "Cap.", "Captain", "Vicount", "Viscount", "Vicounte", "Viscounte", "Apostle", "Monarch", "K.", "Q.", "Saint", "St", "S.", "St.", "Mayor", "Mayore", "Maior", "Maiore"])

first_names = pycorpora.humans.firstNames["firstNames"]
first_names.extend(["Will"])

ordinals = ["First", "Second", "Third", "Fourth", "Fifth", "Sixth", "Seventh", "Eighth", "Ninth", "Tenth", "Eleventh", "Twelfth", "Thirteenth", "Fourteenth", "Fifteenth"]
ofs = ["of", "de", "du"]

# A file of common early modern name abbreviations, for later expansion
with open('data/name_abbrev.json') as abbrevfile:
    abbrev = json.loads(abbrevfile.read())

def is_proper_noun(tag):
    """
    Tests whether a token is marked as a proper noun.
    """
    if tag != None and (tag.get('pos', '') == 'nn1' or tag.get('pos', '') == 'nng1'):
        return True
    else:
        return False

def is_personal_title(tag):
    """
    Tests whether a token is one of the common titles or prefixes
    that accompany a name.
    """
    if tag != None and tag.get('reg', tag.text) in prefixes:
        return True
    else:
        return False

def is_personal_of(tag):
    """
    Tests whether a token is the word "of" surrounded by other probably names,
    meaning that this "of" is likely part of the name, i.e. Duke of Buckingham.
    """
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
    """
    A similar test as the personal of, but for commas that might be part of names.
    """
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
    """
    The same as the comma test above, but for periods.
    """
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
    """
    And the same test again, for the word "the." I could have aggregated all of the above
    functions using regular expressions, but I chose to keep them separate to make everything
    more readable.
    """
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
    """
    A test for whether the token is in the stopwords list and 
    therefore definitively not a personal name.
    """
    if tag.get('reg', tag.text).lower() in stopwords:
        return True
    else:
        return False

def is_abbrev(tag):
    """
    Test whether the token is a possible abbreviation.
    """
    if tag.text != None:
        if tag.get('pos', '') == 'ab' or re.fullmatch(r"[A-Z][a-z]{0,4}\.", tag.get('reg',tag.text)) or re.fullmatch(r"[A-Z]{1,4}\.", tag.get('reg',tag.text)):
            return True
        else: 
            return False
    else:
        False

def is_common_name(tag):
    """
    Test if the token is a common first name.
    """
    if tag != None:
        if tag.text != None and tag.get('reg', tag.text).title() in first_names:
            return True
        else:
            return False
    else:
        return False

def upper_tag(tag):
    """
    Is the token uppercase?
    """
    if tag != None:
        if tag.text != None and tag.get('reg', tag.text).isupper():
            return True
        else:
            return False
    else:
        return False

def title_tag(tag):
    """
    Is the token titlecase?
    """
    if tag != None:
        if tag.text != None and tag.get('reg', tag.text).istitle():
            return True
        else:
            return False
    else:
        return False

def is_royal_numeral(tag):
    """
    Test whether the token is likely some variant on a numeral following
    the name of a monarch.
    """
    if tag != None:
        if tag.text != None and (re.fullmatch(r"[IVX]+\.?|[1-9](r?d\.?|th\.?)", tag.get('reg', tag.text)) or tag.get('reg', tag.text).title() in ordinals):
            return True
        else:
            return False
    else:
        return False

def is_initial(tag):
    """
    Test whether the name is a single initial, i.e. "J."
    """
    if tag != None:
        if tag.text != None and re.fullmatch(r"[A-Z]\.", tag.get('reg', tag.text)):
            return True
        else:
            return False
    else:
        return False

def is_religious(tag, previous_tag):
    """
    A special test for a certain kind of reference to "God" or "Christ" that
    doesn't reference them as people but rather general religious concepts, i.e.
    "love of Christ," "truth of God," "God's will," etc. I filter these out to avoid
    skewing the numbers.
    """
    try:
        if (tag.get("reg", tag.text).lower() == "god" or tag.get("reg", tag.text).lower() == "christ") and previous_tag.get("reg", previous_tag.text) == "of" and (previous_tag.getprevious().get("pos") == "n1" or previous_tag.getprevious().get("pos") == "n2"):
            return True
        else:
            return False
    except AttributeError:
        return False

def is_name(tag):
    """
    Putting together all the above functions, this function is a general test for
    whether a token element is likely part of a name.
    """
    next_tag = tag.getnext()
    previous_tag = tag.getprevious()
    if is_religious(tag, previous_tag):
        return False
    elif is_proper_noun(tag):
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
    elif is_common_name(tag) and (is_proper_noun(next_tag) or is_personal_period(next_tag) or is_personal_title(previous_tag)):
        return True
    elif upper_tag(tag) and ((upper_tag(previous_tag) and (is_proper_noun(previous_tag) or is_personal_title(previous_tag))) or is_personal_of(previous_tag)) and is_not_person(previous_tag) == False:
        return True
    elif title_tag(tag) and is_not_person(tag) == False and ((title_tag(previous_tag) and (is_proper_noun(previous_tag) or is_personal_title(previous_tag))) or is_personal_of(previous_tag)) and is_not_person(previous_tag) == False:
        return True
    elif is_royal_numeral(tag) and (is_proper_noun(previous_tag) or is_personal_the(previous_tag) or is_common_name(previous_tag)):
        return True
    elif is_initial(tag) and (is_initial(previous_tag) or is_initial(next_tag)):
        return True
    else:
        return False

def expand_abbrev(name):
    """
    Expand abbreviations based on list imported above.
    """
    for k,v in abbrev.items():
        patt = f"\\b{k.lower()}\.?\\b"
        name = re.sub(patt, v.lower(), name.lower())
    return name


def fingerprint(name):
    """
    A fingerprinting function that mimics some of the disambiguation features of
    OpenRefine. Originally I intended to use this in place of OpenRefine, but that
    proved less reliable and efficient than using OpenRefine directly. Now this function
    is used primarily to compare possible author names.
    """
    testname = name
    if re.search(r"\bjesu", testname.lower()) != None or re.search(r"\bchrist\b", testname.lower()) != None:
        return ("christ", "")
    else:
        testname = re.sub(r"\band\b|\bor\b", "", testname)
        for k,v in abbrev.items():
            patt = f"\\b{k.lower()}\.?\\b"
            testname = re.sub(patt, v.lower(), testname.lower())
        testname = re.sub(r"\bfl\b|\bof\b|\bd\.|\bb\.", "", testname)
        testname = re.sub(r"[\.\?,!;:\(\)\-\[\]]|'s", "", testname)
        testname = re.sub(r"\d+", "", testname)
        if " " in testname:
            testname = "".join(sorted(testname.split()))
        dm = doublemetaphone(testname)
        if dm[1] == '' and re.search(r"[aiouy]$", testname.lower()) != None:
            return (dm[0], f"{dm[0]}{testname[-1].upper()}")
        elif dm[1] == '' and re.search(r"^b", testname.lower()) != None:
            return (dm[0], f"{testname[0].upper()}{dm[0][1:]}")
        else:
            return dm

def is_author(name, author):
    """
    Using the fingerprint function above, determines whether the name
    is a plausible match for the author's name found in the metadata.
    """
    initials = ''.join([a[0] for a in author.split()])
    if fingerprint(name) == fingerprint(author):
        return True
    elif re.sub(r'\W+', '', name).lower() == re.sub(r'\W+', '', initials).lower():
        return True
    else:
        return False

def get_parents(e):
    """
    Easily get the names of ancestor elements for a given element.
    Used to keep track of where in the dedication a name appears.
    """
    ancestors = [ancestor.tag.split("}")[-1] for ancestor in e.iterancestors()]
    if "signed" in ancestors:
        return "signed"
    elif "head" in ancestors:
        return "head"
    else:
        return "body"

def get_metadata(xml):
    """
    Get metadata information from https://github.com/earlyprint/epmetadata
    """
    author = xml.find(".//ep:author", namespaces=nsmap)
    title = xml.find(".//ep:title", namespaces=nsmap)
    date = xml.find(".//ep:publicationYear", namespaces=nsmap)
    if author is not None:
        author = author.text
    else:
        author = ""
    if title is not None:
        title = title.text
    else:
        title = ""
    if date is not None:
        date = date.text
    else:
        date = ""
    return author, title, date

if __name__ == "__main__":

    start = time.process_time()
    # Open each EarlyPrint XML document
    nsmap={'tei': 'http://www.tei-c.org/ns/1.0', 'ep': 'http://earlyprint.org/ns/1.0'}
    files = glob.glob("/home/data/eebotcp/texts/*/*.xml")
    parser = etree.XMLParser(collect_ids=False)

    # Keep track of edges (name-text connections) and nodes (individual names and texts)
    orig_edges = []
    nodes = []
    for f in files:
        fileid = f.split("/")[-1].split(".")[0]
        tree = etree.parse(f, parser)
        xml = tree.getroot()
        
        # Get the dedication (if there is one) and metadata for each file
        dedications = xml.findall(".//tei:*[@type='dedication']", namespaces=nsmap)
        author, title, date = get_metadata(xml)
        if len(dedications) > 0:
            nodes.append((fileid, {"author": author, "title": title, "date": date}))

        # In each dedication loop through every token
        for dedication in dedications:
            tokens = dedication.xpath(".//tei:w|.//tei:pc", namespaces=nsmap)
            tested = []
            for t in tokens:
                # Make sure that the token is not part of a citation or marginal note
                ancestors = [ancestor.tag.split("}")[-1] for ancestor in t.iterancestors()]
                if "note" not in ancestors and "bibl" not in ancestors:
                    # Test whether each token is a name, using is_name() function
                    # Keep track of parent tags for the token's place in the dedication
                    tested.append((t.get('reg', t.text), is_name(t), get_parents(t)))

            # Group adjacent name-words together into multi-word names
            # Check whether any multi-word names match author names
            for k,g in groupby(tested, key=lambda x:x[1]):
                g = list(g)
                if k == True:
                    name = " ".join([w for w,test,p in g])
                    if is_author(name, author):
                        if re.fullmatch(r"([A-Z]\.\s?){2,}", name):
                            author_name = re.sub(r"\bfl\b|\bd\.|\bb\.", "", author)
                            author_name = re.sub(r"\d+", "", author_name)
                            author_name = author_name.strip(",")
                            orig_edges.append([fileid, author_name, "true", g[0][2]])
                        else:
                            orig_edges.append([fileid, expand_abbrev(name), "true", g[0][2]])
                    elif re.fullmatch(r"([A-Z]\.\s?){2,}", name) == None:
                        orig_edges.append([fileid, expand_abbrev(name), "false", g[0][2]])

    # Export data as TSV file
    with open("test_edges0817.csv", "w") as edgefile:
        writer2 = csv.writer(edgefile, delimiter="\t")
        writer2.writerows(orig_edges)

    # Print the total processing time
    end = time.process_time()
    print(end-start)
