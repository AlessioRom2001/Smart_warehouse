import json

class TelemetryMessage:
    """
    Telemetry Message DTO class
    mapping the telemetry message data structure with:
    - timestamp: timestamp of the telemetry message (optional)
    - data_type: type of the telemetry message (optional)
    - value: value of the telemetry message (required)
    Permette di rappresentare anche messaggi semplici come {'value': 3}.
    """
    def __init__(self, value, timestamp=None, data_type=None):
        self.value = value
        self.timestamp = timestamp
        self.data_type = data_type

    @staticmethod
    def from_dict(data):
        """Crea un oggetto TelemetryMessage da un dizionario, gestendo anche il caso {'value': ...}"""
        value = data.get('value')
        timestamp = data.get('timestamp')
        data_type = data.get('data_type')
        return TelemetryMessage(value, timestamp, data_type)

    def to_json(self):
        # Esporta solo i campi non None
        d = {k: v for k, v in self.__dict__.items() if v is not None}
        return json.dumps(d)