# homeassistant-ariston-sensor


Now moving to https://github.com/julupanter/ariston-remotethermo-home-assistant-v2 a fork of chomupashchuk adapted to work directly with HACS. It has configurable sensors, climate and other and gives services to write data, not only read.


Ariston Net integration with home assistant, for devices using the Ariston Sensys thermostats or similar devices that connect to the ariston remotethermo app https://www.ariston-net.remotethermo.com , also called Ariston Net (apk for mobile devices).

This plugin will add sensors for the main controlled data, and need a configuration in the configuration.yaml file like:
```json
sensor:
  - platform: ariston
    name: Ariston aerotermia
    device_id: !secret ariston_device_id
    username: !secret ariston_user_name
    password: !secret ariston_password
```
Where: 
'name' could be anything you like, 
'device_id' is the id used by the Ariston API, easily find on the web address like https://www.ariston-net.remotethermo.com/PlantDashboard/Index/<DEVICE_ID>. e.g. E5AF4E012546
'username' and 'password' are the credentials on the web page. Typically username will be your email address.

The easiest way to add this module to home assistant is using the 'HACS' plugin, https://github.com/hacs/integration, and adding this repository (julupanter/homeassistant-ariston-sensor) as a custom one.

Anything you want to ask me, please feel free to open an issue (even if its not one).
