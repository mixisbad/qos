#!/bin/bash
#predefine="http://cs.hbg.psu.edu"
first_rec=1
forward_factor=1
prev_req=0
count=0
#exec 1>testlog.out 2>&1
while [ "$count" -le "50" ]
do
STARTTIME=$(date +%s)
./select_queue.py $3 $2 $1 "add" "Q"$2"-"$1"-"$count
wget $1"/"$4
./select_queue.py $3 $2 $1 "del" "Q"$2"-"$1"-"$count
ENDTIME=$(date +%s)
echo $((ENDTIME - STARTTIME))" : "$1" : "$4>>log.out
rm ./$4
count=$((count + 1))
done