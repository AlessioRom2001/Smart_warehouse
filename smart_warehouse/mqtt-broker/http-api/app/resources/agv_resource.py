from flask_restful import Resource, reqparse
from flask import request

class AGVPositionResource(Resource):
    def __init__(self, **kwargs):
        self.data_manager = kwargs.get('data_manager')

    def get(self, agv_id):
        # Recupera la posizione dell'AGV dal data_manager
        warehouse_id = 'default_warehouse'
        agv_positions = self.data_manager.get_agv_positions(warehouse_id) or {}
        if agv_id in agv_positions:
            return agv_positions[agv_id], 200
        else:
            return {'message': f'AGV {agv_id} position not found'}, 404

    def post(self, agv_id):
        data = request.get_json(force=True)
        position = data.get('position')
        timestamp = data.get('timestamp')
        # Recupera le posizioni esistenti o crea un nuovo dict
        warehouse_id = 'default_warehouse'
        agv_positions = self.data_manager.get_agv_positions(warehouse_id) or {}
        agv_positions[agv_id] = {
            'position': position,
            'timestamp': timestamp
        }
        self.data_manager.add_agv_positions(warehouse_id, agv_positions)
        print(f"Received AGV position: {agv_id}, position: {position}, timestamp: {timestamp}")
        return {'message': f'Position for AGV {agv_id} registered successfully.'}, 201
