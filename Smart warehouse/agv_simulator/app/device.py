import json


class Device:
    """ Base class for devices """

    def __init__(self, device_id: str, device_type: str):
        """ Initialize the devices with a devices ID and a devices type """
        self.device_id = device_id
        self.device_type = device_type

    def get_json_measurement(self) -> str:
        """ Returns a JSON representation of the Sensor Status (e.g., the last measurement) """
        raise NotImplementedError("This method should be overridden by subclasses")

    def get_json_description(self) -> str:
        """ Returns a JSON representation of the Sensor Description """

        result_dict = {
            "device_id": self.device_id,
            "device_type": self.device_type,
        }

        return json.dumps(result_dict)