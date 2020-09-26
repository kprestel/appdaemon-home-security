# AppDaemon Home Security

_AppDaemon app for [HACS](https://github.com/custom-components/hacs)._

Provides a home security system based on `binary_sensors`.

*Note this app is still in beta and may not be stable.*

## Installation

Download the `alaram_system` directory from inside the `apps` directory here to your local `apps` directory, then add the configuration to enable the `AlarmSystem` module.

## App configuration

```yaml

alarm_system:
  module: alarm
  class: AlarmSystem
  device_trackers:
    - device_tracker.his_device
    - device_tracker.her_device
    - device_tracker.their_device
  armed_home_binary_sensors:
    - binary_sensor.rear_door_open_closed
    - binary_sensor.living_room_window_sensor_1_open_closed
    - binary_sensor.living_room_window_sensor_2_open_closed
  armed_away_binary_sensors:
    - binary_sensor.entry_way_motion_sensor
  notify_service: mobile_app
  notify_title: "AlarmSystem triggered, possible intruder"
  alarm_arm_home_after_time: "23:15:00"
  alarm_arm_home_before_time: "06:00:00"
  alarm_control_panel: alarm_control_panel.alarm
  alarm_pin: "1234"
```

| key                          | optional | type   | default                    | description                                                                                                                                                                                |
| ---------------------------- | -------- | ------ | -------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `module`                     | False    | string |                            | The module name of the app.                                                                                                                                                                |
| `class`                      | False    | string |                            | The name of the Class.                                                                                                                                                                     |
| `armed_home_binary_sensors`  | False    | string |                            | Binary sensors that if turn `on` while `armed home`, will trigger an alarm                                                                                                                 |
| `armed_away_binary_sensors`  | False    | string |                            | Binary sensors that if turn `on` while `armed away`, will trigger an alarm. Any sensor that is in the `armed_home_binary_sensors` list will be included in the`armed_away_binary_sensors`. |
| `device_trackers`            | True     | string | `None`                     | Device trackers                                                                                                                                                                            |
| `notify_service`             | True     | string | `None`                     | The service to call in the event of an alarm being triggered                                                                                                                               |
| `notify_title`               | True     | string | `None`                     | The title of the notification                                                                                                                                                              |
| `alarm_arm_home_after_time`  | True     | string | `23:15:00`                 | Local time to automatically `arm_home`                                                                                                                                                     |
| `alarm_arm_home_before_time` | True     | string | `06:00:00`                 | Local time to automatically `disarm_home`                                                                                                                                                  |
| `alarm_control_panel`        | True     | string | `alam_control_panel.alarm` | The `hass` alam_control_panel alarm                                                                                                                                                        |
| `alarm_pin`                  | True     | string | `None`                     | The pin to arm/disarm the alarm                                                                                                                                                            |


## Road Map

* Add ability to arm/disarm via buttons

* Add ability to trigger alarm based on more than just `binary_sensors`

* Add ability to execute arbitary services when an alarm is triggered