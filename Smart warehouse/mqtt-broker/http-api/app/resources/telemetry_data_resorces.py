
from json import JSONDecodeError
from flask import request, Response
from flask_restful import Resource
from dto.telemetry_message import TelemetryMessage

class TelemetryDataResource(Resource):
    """Resource to handle the Telemetry Data of a specific Device"""

    def __init__(self, **kwargs):
        # Inject the DataManager instance
        self.data_manager = kwargs['data_manager']

    def get(self, device_id):
        """GET Request to retrieve the Telemetry Data of a target device"""
        device_telemetry_data = self.data_manager.get_telemetry_data_by_device_id(device_id)
        if device_telemetry_data is not None:
            result_location_list = []
            for telemetry_data in device_telemetry_data:
                if isinstance(telemetry_data, TelemetryMessage):
                    result_location_list.append(telemetry_data.__dict__)
                elif isinstance(telemetry_data, dict):
                    result_location_list.append(telemetry_data)
            return result_location_list, 200
        else:
            return {'error': "Device Not Found !"}, 404

    def post(self, device_id):
        try:
            telemetry_data_dict = request.get_json(force=True)
            # Crea un oggetto TelemetryMessage dalla richiesta
            telemetry_message = TelemetryMessage(
                telemetry_data_dict.get('timestamp'),
                telemetry_data_dict.get('data_type'),
                telemetry_data_dict.get('value')
            )
            self.data_manager.add_device_telemetry_data(device_id, telemetry_message)
            return Response(status=201)
        except JSONDecodeError:
            return {'error': "Invalid JSON ! Check the request"}, 400
        except Exception as e:
            return {'error': "Generic Internal Server Error ! Reason: " + str(e)}, 500