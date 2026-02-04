from flask_restful import Resource
from flask import request


class SlotStatusResource(Resource):
    def __init__(self, **kwargs):
        self.data_manager = kwargs.get('data_manager')

    def get(self):
        warehouse_id = 'default_warehouse'
        slot_statuses = self.data_manager.get_slot_statuses(warehouse_id) or {}
        return slot_statuses, 200

    def post(self):
        data = request.get_json(force=True)
        warehouse_id = 'default_warehouse'
        slot_statuses = self.data_manager.get_slot_statuses(warehouse_id) or {}
        # Si aspetta un dizionario {slot_id: dati_slot, ...} oppure una lista di slot
        if isinstance(data, dict):
            slot_statuses.update(data)
        elif isinstance(data, list):
            for slot in data:
                slot_id = slot.get('slot_id')
                if slot_id:
                    slot_statuses[slot_id] = slot
        self.data_manager.add_slot_statuses(warehouse_id, slot_statuses)
        print(f"Received slots batch: {data}")
        return {'message': 'Status for all slots registered successfully.'}, 201
