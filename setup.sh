#!/bin/bash

#install Adafruit BBIO

sudo apt-get update
sudo apt-get install build-essential python-dev python-setuptools python-pip python-smbus -y

sudo pip install Adafruit_BBIO

#install swig

sudo apt-get update
sudo apt-get install swig

#install pixy software

sudo apt-get install libusb-1.0-0.dev
sudo apt-get install libboost-all-dev
sudo apt-get install cmake
git clone https://github.com/charmedlabs/pixy.git

#permissions
chmod u+x ./*.sh

cd pixy/scripts
./build_libpixyusb.sh
sudo ./install_libpixyusb.sh

./build_libpixyusb.sh

./build_pantilt_python_demo.sh

cd ../build/pantilt_in_python

#permissions
chmod u+x ./*.py

python setup.py

mv ~/Tracking.py .

#permissions
chmod u+x ./Tracking.py

#creating protocol to run script at startup
mv ~/startup.sh /usr/bin/

#permissions
chmod u+x /usr/bin/startup.sh

mv ~/startup.service /lib/systemd/

cd /etc/systemd/system/
ln /lib/systemd/<scriptname>.service <scriptname>.service

systemctl daemon-reload
systemctl start <scriptname>.service
systemctl enable <scriptname>.service

shutdown -h now