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

| key                          | optional | type   | default                    | description                                                                |
| ---------------------------- | -------- | ------ | -------------------------- | -------------------------------------------------------------------------- |
| `module`                     | False    | string |                            | The module name of the app.                                                |
| `class`                      | False    | string |                            | The name of the Class.                                                     |
| `armed_home_binary_sensors`  | False    | string |                            | Binary sensors that if turn `on` while `armed home`, will trigger an alarm |
| `armed_away_binary_sensors`  | False    | string |                            | Binary sensors that if turn `on` while `armed away`, will trigger an alarm |
| `device_trackers`            | True     | string | `None`                     | Device trackers                                                            |
| `notify_service`             | True     | string | `None`                     | The service to call in the event of an alarm being triggered               |
| `notify_title`               | True     | string | `None`                     | The title of the notification                                              |
| `alarm_arm_home_after_time`  | True     | string | `23:15:00`                 | Local time to automatically `arm_home`                                     |
| `alarm_arm_home_before_time` | True     | string | `06:00:00`                 | Local time to automatically `disarm_home`                                  |
| `alarm_control_panel`        | True     | string | `alam_control_panel.alarm` | The `hass` alam_control_panel alarm                                        |
| `alarm_pin`                  | True     | string | `None`                     | The pin to arm/disarm the alarm                                            |

