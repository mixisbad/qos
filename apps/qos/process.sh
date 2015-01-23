#!/bin/bash
#predefine="http://cs.hbg.psu.edu"
first_rec=1
forward_factor=1
prev_req=0

while read -r line || [[ -n $line ]]
do
log=$line
ip=${log%%;*}

cut_front=${log#*;}
req_time=${cut_front%;*}

day=${req_time%%/*}
day=${day#[}

hour=${req_time#*:}
hour=${hour%%:*}

min=${req_time%:*}
min=${min##*:}

sec=${req_time##*:}
sec=${sec%% *}


if [ $first_rec -eq 1 ]
then
    sleeptime=0
    first_rec=0
    echo "start right away"

else
    if [ $prev_day -ne $day ]
    then
	prevtime=$(($((10#$prev_hour))*60+$((10#$prev_min))))
	prevtime=$(($((10#$prevtime))*60+$((10#$prev_sec))))
	curtime=$((24*60))
	curtime=$(($((10#$hour))*60+$((10#$min))+$((10#$curtime))))
	curtime=$(($((10#$curtime))*60+$((10#$sec))))
	sleeptime=$(($((10#$curtime))-$((10#$prevtime))))
    else
	prevtime=$(($((10#$prev_hour))*60+$((10#$prev_min))))
	prevtime=$(($((10#$prevtime))*60+$((10#$prev_sec))))
	curtime=$(($((10#$hour))*60+$((10#$min))))
	curtime=$(($((10#$curtime))*60+$((10#$sec))))
	sleeptime=$(($((10#$curtime))-$((10#$prevtime))))
    fi

    current_req=$(date +%s)
    tmpsleep=$((current_req - prev_req))
    if [ $tmpsleep -gt $sleeptime ]
    then
	echo "start right away"
    else
	
	sleep=$((tmpsleep - sleep))
	echo "wait time is : "$((sleeptime / forward_factor))
    fi
fi

echo "./select_queue.py "$3" "$2" "$ip" add"
sleep 2s


prev_day=$day
prev_hour=$hour
prev_min=$min
prev_sec=$sec
    
path=${log##*;}

echo "wget $ip$path -O "$2".out"

echo "./select_queue.py "$3" "$2" "$ip" del"
sleep 2s

prev_req=$current_req



done < $1