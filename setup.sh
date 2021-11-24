#!/bin/bash

cd home/ubuntu

# install dependencies 
sudo apt update && sudo apt upgrade -y
echo "1">>log.txt

sudo apt install postgresql postgresql-contrib -y
echo "2">>log.txt

# cria usuario postgres e um db 
sudo su - postgres
echo "3">>log.txt

echo "cloud" | createuser -s cloud -W
echo "4">>log.txt

createdb -O cloud tasks

# Remova o comentário e substitua a string da linha para aceitar conexões remotas:
# listen_addresses = '*'
sudo sed -i "s/#listen_addresses = 'localhost'/listen_addresses = '*'/g" /etc/postgresql/10/main/postgresql.conf
echo "5">>log.txt

# Adicione a linha que libera qualquer máquina dentro da subnet do kit:
# host all all 192.168.0.0/20 trust
sudo echo host all all 0.0.0.0/0 trust >> /etc/postgresql/10/main/pg_hba.conf
echo "6">>log.txt

# Saia do usuário postgres
cd /
cd home/ubuntu
echo "7">>log.txt

sudo ufw allow 5432/tcp
echo "8">>log.txt

sudo systemctl restart postgresql