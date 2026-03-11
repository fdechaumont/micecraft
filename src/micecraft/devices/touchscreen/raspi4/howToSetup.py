
'''
How to setup the raspberry:

update raspberry pi
if you can't update, an icon will appear on top right of the gui ( blue arrow pointing down in a circle )
turn off bluetooth in the gui (left click -> turn off bluetooth)

in gui > config > turn on serial port, turn off serial console
pip install pygame --upgrade --break-system-packages


add those lines to the /boot/firmware/config.txt with sudo nano /boot/firmware/config.txt


[all]

enable_uart=1

put the screen in 1280x720... anyway the size will adapt if the correct resolution is not found

setting up autostart:

cd /home/fab/.config
mkdir autostart
cd /home/fab/.config/autostart/
nano touchscreen.desktop

add those lines:

[Desktop Entry]
Type=Application
Exec=bash -c "/usr/bin/python3 /home/fab/Desktop/touchscreen/touchscreen.py >/home/fab/Desktop/touchscreen.log.txt"

'''