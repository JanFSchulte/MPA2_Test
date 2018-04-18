stdbuf -oL python ProbeCardTest.py $1 | tee VerboseLogFile.txt &
tail -f ../ProbeStationResults/$1_v$2/VerboseLogFile.txt
