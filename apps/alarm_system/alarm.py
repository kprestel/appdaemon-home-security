import appdaemon.plugins.hass.hassapi as hass

#
# AlarmSystem App
#
# Args:
# armed_home_binary_sensors: binary sensors that if triggred should trigger the alaram when home
# armed_away_binary_sensors: binary sensors that if triggred should trigger the alaram when away
#


class AlarmSystem(hass.Hass):
    def initialize(self):
        self.log("Hello from AlarmSystem")

        # setup sane defaults
        # sensors
        self._armed_home_binary_sensors = self.args.get("armed_home_binary_sensors", [])
        self._armed_away_binary_sensors = self.args.get("armed_away_binary_sensors", [])
        self._armed_away_binary_sensors.extend(self._armed_home_binary_sensors)
        self._device_trackers = self.args.get("device_trackers", [])
        # controls
        self._vacation_control = self.args.get("vacation_control", None)
        self._guest_control = self.args.get("guest_control", None)
        self._alarm_control_panel = self.args.get(
            "alarm_control_panel", "alarm_control_panel.alarm"
        )
        self._alarm_pin = self.args.get("alarm_pin", None)
        self._alarm_volume_control = self.args.get("alarm_volume_control", None)
        self._info_volume_control = self.args.get("info_volume_control", None)
        self._silent_control = self.args.get("silent_control", None)

        # notifications
        self._notify_service = self.args.get("notify_service", None)
        self._notify_title = self.args.get(
            "notify_title", "AlarmSystem triggered, possible intruder"
        )

        # auto arm time
        self._alarm_arm_home_after_time = self.args.get(
            "alarm_arm_home_after_time", "23:15:00"
        )
        self._alarm_arm_home_before_time = self.args.get(
            "alarm_arm_home_before_time", "06:00:00"
        )

        # log current config
        self.log(f"Got armed_home binary sensors {self._armed_home_binary_sensors}")
        self.log(f"Got armed_away binary sensors {self._armed_away_binary_sensors}")
        self.log(f"Got device trackers {self._device_trackers}")
        self.log(
            f"Got {self.count_home_device_trackers()} device_trackers home and {self.count_not_home_device_trackers()} device_trackers not home"
        )
        self.log(f"Got guest_mode {self.in_guest_mode()}")
        self.log(f"Got vacation_mode {self.in_vacation_mode()}")
        self.log(f"Got silent mode {self.in_silent_mode()}")
        self.log(f"Got info volume {self.get_info_volume()}")
        self.log(f"Got alarm volume {self.get_alarm_volume()}")
        self.log(f"Got notify service {self._notify_service}")
        self.log(f"Got alarm state {self.get_alarm_state()}")

        # app notification configuration
        self._alarm_notifciation_color = self.args.get(
            "alarm_notifciation_color", "#2DF56D"
        )

        self.listen_state(
            self.alarm_state_triggered_callback,
            self._alarm_control_panel,
            new="triggered",
        )
        self.listen_state(
            self.alarm_state_from_armed_home_to_pending_callback,
            self._alarm_control_panel,
            old="armed_home",
            new="pending",
        )
        self.listen_state(
            self.alarm_state_from_armed_away_to_pending_callback,
            self._alarm_control_panel,
            old="armed_away",
            new="pending",
        )
        self.listen_state(
            self.alarm_state_from_disarmed_to_pending_callback,
            self._alarm_control_panel,
            old="disarmed",
            new="pending",
        )
        self.listen_state(
            self.alarm_state_disarmed_callback,
            self._alarm_control_panel,
            new="disarmed",
        )
        self.listen_state(
            self.alarm_state_armed_away_callback,
            self._alarm_control_panel,
            new="armed_away",
        )
        self.listen_state(
            self.alarm_state_armed_home_callback,
            self._alarm_control_panel,
            new="armed_home",
        )

        # TODO: add support for buttons to arm and disarm

        # auto arm and disarm
        for i, sensor in enumerate(self._device_trackers):
            self.listen_state(
                self.alarm_arm_away_auto_callback,
                sensor,
                new="not_home",
                old="home",
                duration=15 * 60 + i,
            )
            self.listen_state(
                self.alarm_disarm_auto_callback,
                sensor,
                new="home",
                old="not_home",
                duration=i,
            )
            self.listen_state(
                self.alarm_arm_home_auto_state_change_callback,
                sensor,
                new="home",
                old="not_home",
                duration=15 * 60 + i,
            )

        self._sensor_handles = {}

        # Init system
        self.start_sensor_listeners()

        if self._alarm_arm_home_after_time is not None:
            runtime = self.parse_time(self._alarm_arm_home_after_time)
            self.run_daily(self.alarm_arm_home_auto_timer_callback, runtime)
            self.log(f"Got alarm_arm_home_after_time {runtime}")
        if self._alarm_arm_home_before_time is not None:
            runtime = self.parse_time(self._alarm_arm_home_before_time)
            self.run_daily(self.alarm_disarm_home_auto_timer_callback, runtime)
            self.log(f"Got alarm_arm_home_before_time {runtime}")

        self.log(f"Current alarm_state is {self.get_alarm_state()}")

    def start_sensor_listeners(self):
        self.start_armed_away_binary_sensor_listeners()
        self.start_armed_home_binary_sensor_listeners()

    def start_armed_home_binary_sensor_listeners(self):
        self.log("Starting armed_home binary sensor listeners")
        for sensor in self._armed_home_binary_sensors:
            self.log(f"Starting sensor: {sensor}")
            self._sensor_handles[sensor] = self.listen_state(
                self.trigger_alarm_while_armed_home_callback,
                sensor,
                new="on",
                old="off",
            )

    def start_armed_away_binary_sensor_listeners(self):
        for sensor in self._armed_away_binary_sensors:
            self.log(f"Starting sensor: {sensor}")
            self._sensor_handles[sensor] = self.listen_state(
                self.trigger_alarm_while_armed_away_callback,
                sensor,
                new="on",
                old="off",
            )

    def stop_sensor_listeners(self):
        for handle in self._sensor_handles:
            if self._sensor_handles[handle] is not None:
                self.cancel_listen_state(self._sensor_handles[handle])
                self._sensor_handles[handle] = None

    def count_device_trackers(self, state):
        count = 0
        for sensor in self._device_trackers:
            if self.get_state(sensor) == state:
                count = count + 1
        return count

    def count_home_device_trackers(self):
        return self.count_device_trackers("home")

    def count_not_home_device_trackers(self):
        return self.count_device_trackers("not_home")

    def in_guest_mode(self):
        if self._guest_control is None:
            return False
        return self.get_state(self._guest_control) == "on"

    def in_vacation_mode(self):
        if self._vacation_control is None:
            return False
        return self.get_state(self._vacation_control) == "on"

    def get_alarm_volume(self):
        if self._alarm_volume_control is None:
            return 99
        return int(float(self.get_state(self._alarm_volume_control)))

    def get_info_volume(self):
        if self._info_volume_control is None:
            return 10
        return int(float(self.get_state(self._info_volume_control)))

    def in_silent_mode(self):
        if self._silent_control is None:
            return False
        return self.get_state(self._silent_control) == "on"

    def is_alarm_armed_away(self):
        return self.is_alarm_in_state("armed_away")

    def is_alarm_armed_home(self):
        return self.is_alarm_in_state("armed_home")

    def is_alarm_disarmed(self):
        return self.is_alarm_in_state("disarmed")

    def is_alarm_pending(self):
        return self.is_alarm_in_state("pending")

    def is_alarm_triggered(self):
        return self.is_alarm_in_state("triggered")

    def is_alarm_in_state(self, state):
        if self._alarm_control_panel is None:
            return False
        return self.get_state(self._alarm_control_panel) == state

    def get_alarm_state(self):
        if self._alarm_control_panel is None:
            return None
        return self.get_state(self._alarm_control_panel)

    def is_time_in_alarm_home_window(self):
        return self.now_is_between(
            self._alarm_arm_home_after_time, self._alarm_arm_home_before_time
        )

    def alarm_state_triggered_callback(self, entity, attribute, old, new, kwargs):
        trigger_source_name = self.friendly_name(entity)
        self.log(
            f"Callback alarm_state_triggered from {trigger_source_name}:{attribute} {old}->{new}"
        )

        if self._notify_service is not None:
            self.notify(
                name=self._notify_service,
                title=self._notify_title,
                message=f"ALARM TRIGGED by: {trigger_source_name}",
            )

    def alarm_state_from_armed_home_to_pending_callback(
        self, entity, attribute, old, new, kwargs
    ):
        self.log(
            f"Callback alarm_state_from_armed_home_to_pending from {self.friendly_name(entity)}:{attribute} {old}->{new}"
        )

    def alarm_state_from_armed_away_to_pending_callback(
        self, entity, attribute, old, new, kwargs
    ):
        self.log(
            f"Callback alarm_state_from_armed_away_to_pending from {self.friendly_name(entity)}:{attribute} {old}->{new}"
        )

    def alarm_state_from_disarmed_to_pending_callback(
        self, entity, attribute, old, new, kwargs
    ):
        self.log(
            f"Callback alarm_state_from_disarmed_to_pending from {self.friendly_name(entity)}:{attribute} {old}->{new}"
        )

    def alarm_state_disarmed_callback(self, entity, attribute, old, new, kwargs):
        self.log(
            f"Callback alarm_state_disarmed from {self.friendly_name(entity)}:{attribute} {old}->{new}"
        )

    def alarm_state_armed_away_callback(self, entity, attribute, old, new, kwargs):
        self.log(
            f"Callback alarm_state_armed_away from {self.friendly_name(entity)}:{attribute} {old}->{new}"
        )
        self.start_sensor_listeners()
        self.notify(
            name=self._notify_service,
            title=f"Alarm currently {new}",
            message="Alarm is now armed ",
        )

    def alarm_state_armed_home_callback(self, entity, attribute, old, new, kwargs):
        self.log(
            f"Callback alarm_state_armed_home from {self.friendly_name(entity)}:{attribute} {old}->{new}"
        )
        self.start_sensor_listeners()
        self.notify(
            name=self._notify_service,
            title=f"Alarm currently {new}",
            message="Alarm is now armed home",
        )

    def trigger_alarm_while_armed_away_callback(
        self, entity, attribute, old, new, kwargs
    ):
        self.log(
            f"Callback trigger_alarm_while_armed_away from {self.friendly_name(entity)}:{attribute} {old}->{new}"
        )

        if not self.is_alarm_armed_away():
            self.log(
                f"Ignoring status {new} of {self.friendly_name(entity)} because alarm system is in state {self.get_alarm_state()}"
            )
        elif self.count_home_device_trackers() > 0:
            self.log(
                f"Ignoring status {new} of {self.friendly_name(entity)} because {self.count_home_device_trackers()} device_trackers are still at home"
            )
        else:
            self.trigger_alarm()

    def trigger_alarm_while_armed_home_callback(
        self, entity, attribute, old, new, kwargs
    ):
        self.log(
            f"Callback trigger_alarm_while_armed_home from {self.friendly_name(entity)}:{attribute} {old}->{new}"
        )

        # TODO: need to think through this. would like to have cascading logic where armed_home is just
        # a weaker armed_away
        if not self.is_alarm_armed_home():
            self.log(
                f"Ignoring status {new} of {self.friendly_name(entity)} because alarm system is in state {self.get_alarm_state()}"
            )
        else:
            self.trigger_alarm()

    def alarm_arm_away_state_callback(self, entity, attribute, old, new, kwargs):
        self.log(
            f"Callback alarm_arm_away_state from {self.friendly_name(entity)}:{attribute} {old}->{new}"
        )
        self.arm_away()

    def alarm_disarm_state_callback(self, entity, attribute, old, new, kwargs):
        self.log(
            f"Callback alarm_disarm_state from {self.friendly_name(entity)}:{attribute} {old}->{new}"
        )
        self.disarm()

    def alarm_arm_home_state_callback(self, entity, attribute, old, new, kwargs):
        self.log(
            f"Callback alarm_arm_home_state from {self.friendly_name(entity)}:{attribute} {old}->{new}"
        )
        self.arm_home()

    def alarm_arm_away_event_callback(self, event_name, data, kwargs):
        self.log(
            f"Callback alarm_arm_away_event from {event_name}:{data['entity_id']} {data['click_type']}"
        )

        if self.is_alarm_disarmed():
            self.log(
                f"Ignoring event {event_name} of {data['entity_id']} because alarm system is in state {self.get_alarm_state()}"
            )
        else:
            self.arm_away()

    def alarm_disarm_event_callback(self, event_name, data, kwargs):
        self.log(
            f"Callback alarm_disarm_event from {event_name}:{data['entity_id']} {data['click_type']}"
        )

        if self.is_alarm_disarmed():
            self.log(
                f"Ignoring event {event_name} of {data['entity_id']} because alarm system is in state {self.get_alarm_state()}"
            )
        else:
            self.disarm()

    def alarm_arm_home_event_callback(self, event_name, data, kwargs):
        self.log(
            f"Callback alarm_arm_home_event from {event_name}:{data['entity_id']} {data['click_type']}"
        )

        if self.is_alarm_disarmed():
            self.log(
                f"Ignoring event {event_name} of {data['entity_id']} because alarm system is in state {self.get_alarm_state()}"
            )
        else:
            self.arm_home()

    def arm_home(self):
        self.log("Calling service alarm_control_panel/alarm_arm_home")

        self.call_service(
            "alarm_control_panel/alarm_arm_home",
            entity_id=self._alarm_control_panel,
            code=self._alarm_pin,
        )

    def arm_away(self):
        self.log("Calling service alarm_control_panel/alarm_arm_away")

        self.call_service(
            "alarm_control_panel/alarm_arm_away",
            entity_id=self._alarm_control_panel,
            code=self._alarm_pin,
        )

    def alarm_arm_away_auto_callback(self, entity, attribute, old, new, kwargs):
        self.log(
            f"Callback alarm_arm_away_auto from {self.friendly_name(entity)}:{attribute} {old}->{new}"
        )

        if self.is_alarm_disarmed():
            self.log(
                f"Ignoring status {new} of {self.friendly_name(entity)} because alarm system is in state {self.get_alarm_state()}"
            )
        elif self.count_home_device_trackers() > 0:
            self.log(
                f"Ignoring status {new} of {self.friendly_name(entity)} because {self.count_home_device_trackers()} device_trackers are still at home"
            )
        elif self.in_guest_mode():
            self.log(
                f"Ignoring status {new} of {self.friendly_name(entity)} because {self.count_home_device_trackers()} we have guests"
            )
        else:
            self.log("Calling service alarm_control_panel/alarm_arm_away")
            self.call_service(
                "alarm_control_panel/alarm_arm_away",
                entity_id=self._alarm_control_panel,
                code=self._alarm_pin,
            )

    def alarm_disarm_auto_callback(self, entity, attribute, old, new, kwargs):
        self.log(
            f"Callback alarm_disarm_auto from {self.friendly_name(entity)}:{attribute} {old}->{new}"
        )

        if self.is_alarm_disarmed():
            self.log(
                f"Ignoring status {new} of {self.friendly_name(entity)} because alarm system is in state {self.get_alarm_state()}"
            )
        else:
            self.disarm()

    def alarm_arm_home_auto_state_change_callback(
        self, entity, attribute, old, new, kwargs
    ):
        self.log(
            f"Callback alarm_arm_home_auto_device_change from {self.friendly_name(entity)}:{attribute} {old}->{new}"
        )

        self.alarm_arm_home_auto()

    def alarm_arm_home_auto_timer_callback(self, kwargs):
        self.log("Callback alarm_arm_home_auto_timer")

        self.alarm_arm_home_auto()

    def alarm_disarm_home_auto_timer_callback(self, kwargs):
        self.log("Callback alarm_disarm_home_auto_timer")

        self.alarm_disarm_home_auto()

    def alarm_arm_home_auto(self):
        self.log("Running alarm_arm_home_auto")

        if self.is_alarm_disarmed():
            self.log(
                f"Ignoring because alarm system is in state {self.get_alarm_state()}"
            )
        elif self.count_home_device_trackers() == 0:
            self.log(
                f"Ignoring because all {self.count_not_home_device_trackers()} device_trackers are still away"
            )
        elif self.in_guest_mode():
            self.log(
                f"Ignoring because {self.count_home_device_trackers()} we have guests"
            )
        elif self.is_time_in_alarm_home_window():
            self.log("Ignoring because we are not within alarm home time window")
        else:
            self.log("Calling service alarm_control_panel/alarm_arm_home")
            self.call_service(
                "alarm_control_panel/alarm_arm_home",
                entity_id=self._alarm_control_panel,
                code=self._alarm_pin,
            )

    def alarm_disarm_home_auto(self):
        self.log("Running alarm_disarm_home_auto")
        self.disarm()

    def disarm(self):
        self.log("Calling service alarm_control_panel/alarm_disarm")

        self.call_service(
            "alarm_control_panel/alarm_disarm",
            entity_id=self._alarm_control_panel,
            code=self._alarm_pin,
        )

    def trigger_alarm(self):
        self.log("Calling service alarm_control_panel/alarm_trigger")

        self.call_service(
            "alarm_control_panel/alarm_trigger", entity_id=self._alarm_control_panel
        )