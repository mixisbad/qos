#!/bin/bash
#predefine="http://cs.hbg.psu.edu"
first_rec=1
forward_factor=1
prev_req=0
count=0

while true; do

printf "./select_queue.py "$3" "$2" "$1" add Q"$2"-"$1"-"$count"\n"
./select_queue.py $3 $2 $1 "add" "Q"$2"-"$1"-"$count

wget $1"/file5000k.jpg" >> "wget"$2".txt"

printf "./select_queue.py "$3" "$2" "$1" del Q"$2"-"$1"-"$count"\n"
./select_queue.py $3 $2 $1 "del" "Q"$2"-"$1"-"$count

$count = $((count + 1))
$count = $((count % 1000))

done