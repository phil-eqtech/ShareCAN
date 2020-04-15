# ShareCAN

## DESCRIPTION
As many tools exists to play and read CAN frames, no one allow user to easily read/sniff messages on CANBUS, set gateway and quickly edit .dbc files

This tool, in earlier stage of development, allows user to share analysis and findings on vehicles, grouping results by manufacturers/models/engine.


## USAGE
Type 'python3 app.py' to launch the application


## DEPENDENCIES
The following dependencies are required :
- Python 3
- MongoDB
- can-utils (Linux)


## INSTALLATION
To install the app on any Debian 64 bits launch install.sh

Raspberry version need pymongo 3.4.0 (pip3 install 'pymongo==3.4.0') and a few fixes

Once the install is done, you have to edit "/etc/sudoers" to add the following lines :

`YOUR_USER_NAME	ALL=(ALL) NOPASSWD: /bin/ip, /sbin/ip, /usr/bin/slcand, /sbin/ifconfig`

This allow the application to be run without sudo, as super-user access are only needed to set CAN interfaces.
