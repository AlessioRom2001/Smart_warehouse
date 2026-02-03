from device import Device
import json


class Actuator(Device):
    """ Base class for actuators """

    def __init__(self, device_id: str, device_type: str):
        """ Initialize the actuator with a devices ID and a devices type """
        super().__init__(device_id, device_type)

        # Initialize the status to None, subclasses should set the status when needed
        self.status = "off"

        # Set the timestamp to None, subclasses should set the timestamp when updating the status
        self.timestamp = None

    def invoke_action(self, action_type: str, payload: str) -> None:
        """ Invoke an action on the actuator """
        raise NotImplementedError("This method should be overridden by subclasses")

    def get_json_measurement(self) -> str:
        """ Returns a JSON representation of the Sensor Status (e.g., the last measurement) """
        result_dict = {
            "device_id": self.device_id,
            "status": self.status,
            "timestamp": self.timestamp
        }

        return json.dumps(result_dict)