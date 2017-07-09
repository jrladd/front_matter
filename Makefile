download: src/parse_metadata.py
	./src/parse_metadata.py
	sh src/get_files.sh
	mv *.xml data/1640s_xml

xmltotxt: src/process_xml.py
	./src/process_xml.py

# This won't work in Make, but these are the steps to MorphAdorn the files
morphadorn: data/1640s_txt/*.txt
	cd ../morphadorner
	./adornplainemetext ../front_matter/data/ma_outputs ../front_matter/data/1640s_txt/*.txt
	cd ../front_matter

searchsdfb: src/count_names.sh data/sdfb_names.txt
	./src/count_names.sh

ner: src/ner.py
	./src/ner.py
