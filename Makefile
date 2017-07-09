download: src/parse_metadata.py
	./src/parse_metadata.py
	sh src/get_files.sh
	mv *.xml data/1640s_xml

xmltotxt: src/process_xml.py
	./src/process_xml.py
