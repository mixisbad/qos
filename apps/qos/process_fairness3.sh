#!/bin/bash
count=0
while [ "$count" -le "500" ]
do
./select_queue.py $3 $2 $1 "add" "Q"$2"-"$1"-"$count
echo $1>>log.out
iperf -c $1 -t 30 >> $4
./select_queue.py $3 $2 $1 "del" "Q"$2"-"$1"-"$count
count=$((count + 1))
echo $count
done