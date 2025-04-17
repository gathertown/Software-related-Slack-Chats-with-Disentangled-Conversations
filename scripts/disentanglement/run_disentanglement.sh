#!/bin/bash

set -e

inputs=($(ls -d "$PWD/../../../prepare-thread-dataset/slack_output/"*))

#in_unigrams='elsner-charniak-08-mod/data/linux-unigrams.dump'
in_unigrams='corpora/unigram.txt'

in_techwords='elsner-charniak-08-mod/data/techwords.dump'
predictions_file_name='predictions'
max_sec='1477'


export PYTHONHASHSEED=0
export PYTHONPATH=.
export PYTHONPATH=$PYTHONPATH:$PWD/elsner-charniak-08-mod
export PYTHONPATH=$PYTHONPATH:$PWD/elsner-charniak-08-mod/analysis
export PYTHONPATH=$PYTHONPATH:$PWD/elsner-charniak-08-mod/utils
export PYTHONPATH=$PYTHONPATH:$PWD/elsner-charniak-08-mod/viewer
export PATH=$PATH:$PWD/elsner-charniak-08-mod/megam_0.92


for ((i=0; i<${#inputs[@]}; i++))
do 
	filename=$(basename ${inputs[$i]})
	echo "*** slack-specific preprocessing (${inputs[$i]}) into ${filename}.pre"
	python3 preprocessing/preprocessChat.py -o ${filename}.pre -i ${inputs[$i]}

	echo '*** extracting features'
	rm -fR ${filename}.dir
	python2.7 elsner-charniak-08-mod/model/classifierTest.py corpora/training.annot ${filename}.pre $in_unigrams $in_techwords ${filename}.dir

	if [ ! -e elsner-charniak-08-mod/megam_0.92/megam ]; then
		echo '*** using randomforest instead of megam'
		python3 randomforest/doRandomForest.py ${filename}.dir/$max_sec
	fi

	echo '*** running greedy.py'
	python2.7 elsner-charniak-08-mod/model/greedy.py ${filename}.pre ${filename}.dir/$max_sec/$predictions_file_name ${filename}.dir/$max_sec/devkeys > ${filename}.dnt

	echo '*** reverting preprocessing'
	python3 postprocessing/revert_preprocessing.py ${filename}.dnt ${inputs[$i]} ${filename}.out
	exit 0
done	
