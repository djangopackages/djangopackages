#!/bin/bash
apt-get update
apt-get upgrade -y

# install prerequisites
apt-get install -y git supervisor apt-transport-https ca-certificates linux-image-extra-$(uname -r) apparmor
apt-key adv --keyserver hkp://p80.pool.sks-keyservers.net:80 --recv-keys 58118E89F3A912897C070ADBF76221572C52609D

# install docker
touch /etc/apt/sources.list.d/docker.list
echo "deb https://apt.dockerproject.org/repo ubuntu-xenial main" >> /etc/apt/sources.list.d/docker.list

apt-get update
apt-get purge lxc-docker
apt-cache policy docker-engine

apt-get update
apt-get install docker-engine

service docker start

# install docker compose
curl -L https://github.com/docker/compose/releases/download/1.6.0/docker-compose-`uname -s`-`uname -m` > /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# configure supervisor
sed -i '$ d' /etc/supervisor/supervisord.conf
echo "files = /code/*/supervisord.conf /code/*/docker-supervisord.conf" >> /etc/supervisor/supervisord.conf

# clone repo
mkdir /code
cd /code
git clone https://github.com/pydanny/djangopackages.git

# reload supervisor
supervisorctl reload
