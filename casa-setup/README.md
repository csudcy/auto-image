# Update
```
sudo apt update
sudo apt full-upgrade
sudo reboot
```


# Setup `rpi-connect`
```
rpi-connect signin
```


# Setup Casa
Extract `mm.zip` to `/DATA/mm/`
```
curl -fsSL https://get.casaos.io | sudo bash
```
Import 2x yaml files to Casa


# Install DisplayLink Driver
**This broke RPi connect**
```
wget https://www.synaptics.com/sites/default/files/Ubuntu/pool/stable/main/all/synaptics-repository-keyring.deb
sudo apt install ./synaptics-repository-keyring.deb
sudo apt update
sudo apt full-upgrade
sudo apt install displaylink-driver

# Remove
sudo apt remove displaylink-driver evdi
dkms install ???
```


# Add MM Settings
- Create your own config:
```
cd casa-setup/mm/config
cp config.template.js config.js
```
- Search for `SETUP:` in `config.js` & add your values
- Copy `mm` directory to `/DATA/mm/`


# Add to Casa
- Add a new service & import `Magic Mirror.yaml` (just confirm the settings MM adds)
- [TODO] Add MMPM

# Install MM modules
- `MMM-anotherNewsFeed`
- `MMM-mmpm`
- [TODO] [MMM-DropboxPictures](https://github.com/MMRIZE/MMM-DropboxPictures)
- [TODO] [MMM-CalendarWeek](https://github.com/heskja/MMM-CalendarWeek)


# Setup Kiosk mode
```
sudo nano ~/.config/wayfire.ini
```
Add:
```
[autostart]
chromium = chromium-browser http://casa.local:8080 --kiosk --noerrdialogs --disable-infobars --no-first-run --ozone-platform=wayland --enable-features=OverlayScrollbar --start-maximized
screensaver = false
dpms = false
```
**This breaks RPi connect & the taskbar**


# Auto hide mouse
https://raspberrypi.stackexchange.com/questions/145382/remove-hide-mouse-cursor-when-idle-on-rasbperry-pi-os-bookworm
```
cd ~
mkdir wayfire
cd wayfire
wget https://github.com/seffs/wayfire-plugins-extra-raspbian/releases/download/v0.7.5/wayfire-plugins-extra-raspbian-aarch64.tar.xz
tar xf wayfire-plugins-extra-raspbian-aarch64.tar.xz

sudo cp usr/lib/aarch64-linux-gnu/wayfire/libhide-cursor.so /usr/lib/aarch64-linux-gnu/wayfire/libhide-cursor.so
sudo cp usr/share/wayfire/metadata/hide-cursor.xml /usr/share/wayfire/metadata/hide-cursor.xml

sudo nano ~/.config/wayfire.ini
```
Add:
```
[core]
plugins = \
    autostart \
    hide-cursor
```