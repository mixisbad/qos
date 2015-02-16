#!/bin/bash
#predefine="http://cs.hbg.psu.edu"
first_rec=1
forward_factor=1
prev_req=0
count=0
exec 1>testlog.out 2>&1
while [ $count -lt 100 ]
do
printf "./select_queue.py "$3" "$2" "$1" add Q"$2"-"$1"-"$count"\n"
./select_queue.py $3 $2 $1 "add" "Q"$2"-"$1"-"$count
STARTTIME=$(date +%s)
wget $1"/file1000k.jpg"
ENDTIME=$(date +%s)
echo $((ENDTIME - STARTTIME))" : "$1" : 1000k.jpg">>log.out
printf "./select_queue.py "$3" "$2" "$1" del Q"$2"-"$1"-"$count"\n"
./select_queue.py $3 $2 $1 "del" "Q"$2"-"$1"-"$count

$count=$((count + 1))

done