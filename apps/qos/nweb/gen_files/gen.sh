#!/bin/bash
i=0
while [ $i -le 50 ]
do
    dd if=/dev/zero of='file'$i'00k.blob' bs=$(( i * 102400 )) count=1
    i=$[$i+5]
done