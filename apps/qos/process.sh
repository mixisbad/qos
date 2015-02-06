#!/bin/bash
#predefine="http://cs.hbg.psu.edu"
first_rec=1
forward_factor=1
prev_req=0
count=0

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
	
	sleeptime=$((tmpsleep - sleep))
	echo "wait time is : "$((sleeptime / forward_factor))
	sleep $sleeptime"s"
    fi
fi

printf "./select_queue.py "$3" "$2" "$ip" add Q"$2"-"$ip"-"$count"\n"
./select_queue.py $3 $2 $ip "add" "Q"$2"-"$ip"-"$count
#printf "add Q"$2"-"$ip"-"$count"\n"
sleep 2s


prev_day=$day
prev_hour=$hour
prev_min=$min
prev_sec=$sec
    
path=${log##*;}

#wget $ip$path
printf "wget "$ip$path"\n"

sleep 20s

printf "./select_queue.py "$3" "$2" "$ip" del Q"$2"-"$ip"-"$count"\n"
./select_queue.py $3 $2 $ip "del" "Q"$2"-"$ip"-"$count
#printf "del Q"$2"-"$ip"-"$count"\n"
sleep 2s

prev_req=$current_req

count=$((count + 1))
count=$((count % 100))

done < $1