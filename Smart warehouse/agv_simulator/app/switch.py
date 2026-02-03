from actuator import Actuator
import time


class Switch(Actuator):
    """ Class representing a Switch Actuator """

    # Static Class's attributes used to define action types and values
    STATUS_ON: str = "ON"
    STATUS_OFF: str = "OFF"
    ACTUATOR_TYPE: str = "iot.actuator.switch"
    ACTION_TYPE_SWITCH: str = "SWITCH"

    def __init__(self, device_id: str):
        """ Initialize the smart light with a devices ID and an initial state """
        super().__init__(device_id, Switch.ACTUATOR_TYPE)

        # Set the initial state of the smart light to off
        self.status = Switch.STATUS_OFF

        # Set the timestamp to None, subclasses should set the timestamp when updating the status
        self.timestamp = int(time.time() * 1000)

    def invoke_action(self, action_type: str, payload: str) -> None:
        """ Invoke an action on the smart light """

        # Check if action_type Type and payload are Strings
        if not isinstance(action_type, str) or not isinstance(payload, str):
            raise ValueError("Action type and payload must be strings")

        # Check the action type and payload
        if action_type.upper() == Switch.ACTION_TYPE_SWITCH and payload.upper() in [Switch.STATUS_ON, Switch.STATUS_OFF]:
            self.status = payload
        else:
            raise ValueError("Unsupported action type")