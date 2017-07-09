#! env/bin/python

import spacy, glob


nlp = spacy.load('en', parser=False)

files = glob.glob("data/1640s_txt/*.txt")
texts = [open(f, "r").read() for f in files]

all_names = []
for doc in nlp.pipe(texts):
    names = []
    for ent in doc.ents:
        if ent.label_ == "PERSON" and " " in ent.orth_:
            names.append(ent.orth_)
    all_names.append(names)

names_by_text = {}
for k,v in zip(files, all_names):
    if k[15:-6] not in names_by_text:
        names_by_text[k[15:-6]] = v
    else:
        names_by_text[k[15:-6]].extend(v)

print(names_by_text)
