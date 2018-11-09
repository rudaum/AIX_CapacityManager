servers="sindbad ibaz parisade ibcomtest salomo alibaba maruf ibedi1 ibedi2 ibedi3 ibedi4 ibcom1 ibcom2 ibcom3"
for server in $servers; do
    echo "--- $(date +'%d/%m/%Y %H:%M:%S') Collecting data from $server" > ~ansible/capacity_report/logs/$server.log
    python ~ansible/capacity_report/capacity_collector.py -s $server >> ~ansible/capacity_report/logs/$server.log 2>&1
    echo "--- $(date +'%d/%m/%Y %H:%M:%S') Complete!" >> ~ansible/capacity_report/logs/$server.log
done
