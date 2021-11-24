#!/bin/bash

cd home/ubuntu
sudo apt update
echo "1">>log.txt

git clone https://github.com/thalials/tasks.git    
echo "2">>log.txt

sudo sed -i 's/node1/{0}/' /home/ubuntu/tasks/portfolio/settings.py
echo "3">>log.txt

cd tasks
./install.sh    
cd ..
echo "4">>log.txt

sudo reboot