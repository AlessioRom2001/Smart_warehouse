from flask_restful import Resource, reqparse
from flask import request

class WarehouseParameterResource(Resource):
    def __init__(self, **kwargs):
        self.data_manager = kwargs.get('data_manager')

    def get(self, parameter):
        # Recupera il valore del parametro dal data_manager
        # Per semplicità, usiamo 'default_warehouse' come chiave
        warehouse_id = 'default_warehouse'
        params = self.data_manager.get_warehouse_parameters(warehouse_id)
        if params and parameter in params:
            return {'value': params[parameter]}, 200
        else:
            return {'message': f'Parameter {parameter} not found'}, 404

    def post(self, parameter):
        data = request.get_json(force=True)
        value = data.get('value')
        timestamp = data.get('timestamp')
        data_type = data.get('data_type')
        warehouse_id = 'default_warehouse'
        # Recupera i parametri esistenti o crea un nuovo dict
        params = self.data_manager.get_warehouse_parameters(warehouse_id) or {}
        params[parameter] = value
        self.data_manager.add_warehouse_parameters(warehouse_id, params)
        print(f"Received parameter: {parameter}, value: {value}, timestamp: {timestamp}, data_type: {data_type}")
        return {'message': f'Parameter {parameter} registered successfully.'}, 201
