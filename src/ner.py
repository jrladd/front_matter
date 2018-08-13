#! /usr/bin/env python3.6

import spacy, glob, sys, csv
from process_ma import clean
from spacy import displacy

input_dir = sys.argv[1]


nlp = spacy.load('en', parser=False)

files = glob.glob(input_dir+"*.txt")
texts = [clean(open(f, "r").read()) for f in files]

all_data = []
for doc in nlp.pipe(texts):
    entities = []
    # for ent in doc.ents:
    #     if ent.label_ == "PERSON" and " " in ent.orth_:
    #         entities.append((ent.text, ent.start_char, ent.end_char, ent.label_))
    # all_data.append((doc, {'entities': entities}))
    displacy.serve(doc, style='ent')

print(all_data)

    #         names.append(ent.orth_)
    # all_names.append(names)

# names_by_text = {}
# for k,v in zip(files, all_names):
#     filename = k.split("/")[-1][:-6]
#     if filename not in names_by_text:
#         names_by_text[filename] = v
#     else:
#         names_by_text[filename].extend(v)
#
# dir_name = input_dir[5:-1]
# with open("data/"+dir_name+"_edgelist.csv", "w") as edgelist:
#     writer = csv.writer(edgelist, delimiter="\t")
#     for k,v in names_by_text.items():
#         if len(v) != 0:
#             for name in v:
#                 writer.writerow([k,name])
