#!/bin/bash
count=0
while [ "$count" -le "500" ]
do
./select_queue.py $3 $2 $1 "add" "Q"$2"-"$1"-"$count
wget -O $2file10m.jpg $1/file10m.jpg >> $4
./select_queue.py $3 $2 $1 "del" "Q"$2"-"$1"-"$count
count=$((count + 1))
echo $count
done