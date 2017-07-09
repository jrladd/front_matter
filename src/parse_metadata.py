#! env/bin/python

import sqlite3

conn = sqlite3.connect("data/eebo_tcp_metadata.sqlite")

c = conn.cursor()

c.execute("SELECT key,date FROM metadata WHERE date < 1649 and date >= 1639 and phase = 1;")
results = c.fetchall()

print(len(results))

with open("src/get_files.sh", "w") as newfile:
    for r in results:
        newfile.write("wget https://raw.githubusercontent.com/textcreationpartnership/"+r[0]+"/master/"+r[0]+".xml\n")

print("File written! Downloading now...")
