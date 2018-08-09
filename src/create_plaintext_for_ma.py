#! /usr/bin/env python3

from bs4 import BeautifulSoup
import glob, sys

if __name__ == "__main__":
    input_dir = sys.argv[1]
    output_dir = sys.argv[2]
    xmlfiles = glob.glob(input_dir+"*.xml")
    for x in xmlfiles:
        filename = x.split('/')[-1]
        filekey = filename.split('.')[0]
        with open(x, "r") as xmlfile:
            print("Reading file...")
            soup = BeautifulSoup(xmlfile.read(), "xml")
            dedications = soup.select("[TYPE='dedication']")
            if len(dedications) > 0:
                print("Found dedications...")
                for i,dedication in enumerate(dedications):
                    signed = dedication.select('SIGNED')
                    for s in signed:
                        signed_fn = filekey + '_' + str(i) + '_signed.txt'
                        with open(output_dir+signed_fn, 'w') as signedfile:
                            signedfile.write(s.text)
                        s.extract()
                    dedicatee_names = []
                    head = dedication.select('HEAD')
                    for h in head:
                        head_fn = filekey + '_' + str(i) + '_head.txt'
                        with open(output_dir+head_fn, 'w') as headfile:
                            headfile.write(h.text)
                        h.extract()
                    # print("Other names:")
                    body_fn = filekey + '_' + str(i) + '_body.txt'
                    with open(output_dir+body_fn, 'w') as bodyfile:
                        bodyfile.write(dedication.text)
                    print("wrote dedication!")
