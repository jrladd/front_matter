#! env/bin/python

import glob, csv

files = glob.glob("data/ma_outputs/*.txt")

for f in files:
    with open(f, "r") as csvfile:
        reader = csv.reader(csvfile, delimiter="\t")

        tokens = [r[3] for r in reader]
        reg_string = ' '.join(tokens)
    print(reg_string)
    with open("data/1640s_regularized/"+f[16:], "w") as writefile:
        writefile.write(reg_string)
