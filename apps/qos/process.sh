#!/bin/bash
predefine="http://cs.hbg.psu.edu"
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

OUTPUT="$(./qospath2.py -a -N "Q01-09" -c 10.0.2.15 -S 10.0.0.1 -D 10.0.0.9 -J '{"eth-type":"0x0800","protocol":"6","queue":"2"}')"
echo "${OUTPUT}"

OUTPUT="$(./qospath2.py -a -N "Q09-01" -c 10.0.2.15 -S 10.0.0.9 -D 10.0.0.1 -J '{"eth-type":"0x0800","protocol":"6","queue":"2"}')"
echo "${OUTPUT}"

prev_day=$day
prev_hour=$hour
prev_min=$min
prev_sec=$sec
    
path=${log##*;}
prev_req=$current_req

echo "SIZE "$predefine$path
sleep 5s

OUTPUT="$(./qospath2.py -d -N "Q01-09" -c 10.0.2.15)"
echo "${OUTPUT}"
OUTPUT="$(./qospath2.py -d -N "Q09-01" -c 10.0.2.15)"
echo "${OUTPUT}"

done < $1