Pi Manager, similar to prometheus but uses influxDB.  
However, i think if i setup prometheus completely. it will also  
use the same grafana and other packages that make graphing easier.  



cd to docker_frontend  
docker-compose up --build -d  

Take note of the location of "pi_mngr/send_status.py"  
modify the config file to point to the influxdb  
*note that the influxdb here is provided by: https://github.com/influxdata/TICK-docker*   

open cron with [crontab -e]  
Add the following:  
-  */10 * * * * python [path to send_status.py] 

This will send an update every 10 minutes

