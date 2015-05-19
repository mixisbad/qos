#!/bin/bash
count=0
while [ "$count" -le "500" ]
do
iperf -c $1 -t 30 >> $4
count=$((count + 1))
echo $count
done