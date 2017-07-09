############
# This script takes searches txt files against a list of names
# and produces a single file concatenating all files that match at least 1 of the names.
# It executes in parallel.
# It is **entirely** based on a script by David Walling at
# Github repot sdfb/sdfb_network/code/hpc/text_processing/count_names.sh
###########

# Input
DOCS_PATH=data/1640s_txt
NAMES_FILE=data/sdfb_names.txt

# Temp and Output
MATCHING_FILES=data/name_matches.txt

# First use parallel grep to find all files matching at least 1 of the names.
echo "grepping $NAMES_FILE at $DOCS_PATH"

# Output the filename and matched regex name as: /path/to/filename.txt:regex_name

# NOTE: Requires updated 'parallel' program (developed w/ version 20161222)
# source ~/software/sourceme.sh # Update PATH to use specific parallel version

ls $DOCS_PATH/* | parallel grep -o -F -H -f $NAMES_FILE | tee $MATCHING_FILES
