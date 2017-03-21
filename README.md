# ABC

To setup Automated Ball Collector:
1) Follow setup in
2) Ensure that the latest Debian image has been flashed to the BeagleBone Black (http://derekmolloy.ie/write-a-new-image-to-the-beaglebone-black/)
3) Follow the instructions at http://beagleboard.org/getting-started to set up the board
4)  Using a USB hub, connect your keyboard, mouse, and Pixy to the BeagleBone Black. Using an Ethernet cable, connect your BeagleBone Black to the internet. Connect a video display to the BeagleBone Black using an HDMI cable. Power up the BeagleBone Black using either a USB cable or the 5V barrel connector.
5) Login to the board with the username "root" and type: git clone https://github.com/MASells/ABC.git
6) Type: ./setup.sh, this will install all software dependancies and configure files to be run on subsequent startups. The end of this file will shutdown the board
7) The Tracking.py program will now run on startup
