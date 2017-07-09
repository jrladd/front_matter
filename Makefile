download: src/parse_metadata.py
	./src/parse_metadata.py
	sh src/get_files.sh
	mv *.xml data/1640s_xml
