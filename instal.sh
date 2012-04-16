#!/bin/bash

rm "/usr/lib/gnome-panel/testapplet.py"
rm "/usr/lib/bonobo/servers/SampleApplet_Factory.server"

ln -s "$(pwd)/testapplet.py" "/usr/lib/gnome-panel/testapplet.py"
chmod a+x /usr/lib/gnome-panel/testapplet.py

cp SampleApplet_Factory.server /usr/lib/bonobo/servers/
cp "$(pwd)/phonetic.png" /usr/share/pixmaps/
