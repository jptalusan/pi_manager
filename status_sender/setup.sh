#assuming pip is correctly installed.
#sudo apt-get remove python-pip
#else sudo easy_install pip

sudo pip install psutil flatten_json influxdb

#crontab
echo "Adding */10 * * * * python ~/pi_mngr/send_status.py to crontab, triggers every 10 minutes"

line="*/10 * * * * python ~/pi_mngr/send_status.py"

(crontab -l ; echo "$line")| crontab -
