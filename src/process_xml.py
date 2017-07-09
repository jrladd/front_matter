#! env/bin/python

from bs4 import BeautifulSoup
import glob

xmlfiles = glob.glob("data/1640s_xml/*.xml")

for x in xmlfiles:
    with open(x, "r") as xmlfile:
        soup = BeautifulSoup(xmlfile.read(), "xml")
        dedications = soup.select("[type='dedication']")
    if len(dedications) > 0:
        for i,d in enumerate(dedications):
            with open("data/1640s_txt/"+x[15:-4]+"-"+str(i)+".txt", "w") as txtfile:
                txtfile.write(d.text)
            print("Wrote file for ", x[15:-4])
    else:
        print("No dedication found")
