download: src/parse_metadata.py
	./src/parse_metadata.py
	sh src/get_files.sh
	mv *.xml data/1640s_xml

xmltotxt: src/create_plaintext_for_ma.py
	./src/create_plaintext_for_ma.py

# This won't work in Make, but these are the steps to MorphAdorn the files
morphadorn: data/1640s_txt/*.txt
	cd ../morphadorner
	./adornplainemetext ../front_matter/data/ma_outputs ../front_matter/data/1640s_txt/*.txt
	cd ../front_matter
	rm data/ma_split_outputs/ma_split_outputs

ner_network: src/process_ma.py
	./src/process_ma.py
	
####################################################
## OLD PIPELINE FUNCTIONS
####################################################

# searchsdfb: src/count_names.sh data/sdfb_names.txt
# 	./src/count_names.sh
#
# ner_orig: src/ner.py
# 	./src/ner.py data/1640s_txt/
#
# ner_reg: src/ner.py
# 	./src/ner.py data/1640s_regularized/
#
# fix_names: src/expand_names.py
# 	./src/expand_names.py
#
# # Hand curation to eliminate obvious non-names, add edge types
# #
# expand_names: src/kwic.py #Expand names based on what's around them
# 	./src/kwic.py
#
# # More hand curation, and also finding matches in open refine
# #
# initialize_network: src/initialize_network.py
# 	./src/initialize_network.py
