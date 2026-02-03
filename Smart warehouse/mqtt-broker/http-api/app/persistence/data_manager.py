class DataManager:
    """
    DataManager class is responsible for managing the data of the application.
    Abstracts the data storage and retrieval operations.
    In this implementation everything is stored in memory.
    """


    # The data structure to store the telemetry data
    device_timeseries_data = {}
    # The data structure to store warehouse parameters
    warehouse_parameters = {}
    # The data structure to store AGV positions
    agv_positions = {}
    # The data structure to store slot statuses
    slot_statuses = {}

    def add_device_telemetry_data(self, device_id, telemetry_data):
        """Add a new telemetry data for a given device"""
        if device_id not in self.device_timeseries_data:
            self.device_timeseries_data[device_id] = []
        self.device_timeseries_data[device_id].append(telemetry_data)

    def add_warehouse_parameters(self, warehouse_id, parameters):
        """Add or update parameters for a given warehouse"""
        self.warehouse_parameters[warehouse_id] = parameters

    def add_agv_positions(self, warehouse_id, positions):
        """Add or update AGV positions for a given warehouse"""
        self.agv_positions[warehouse_id] = positions

    def add_slot_statuses(self, warehouse_id, statuses):
        """Add or update slot statuses for a given warehouse"""
        self.slot_statuses[warehouse_id] = statuses

    def get_telemetry_data_by_device_id(self, device_id):
        """Return the telemetry data for a given device"""
        if device_id in self.device_timeseries_data:
            return self.device_timeseries_data[device_id]
        else:
            return None

    def get_warehouse_parameters(self, warehouse_id):
        """Return the parameters for a given warehouse"""
        return self.warehouse_parameters.get(warehouse_id, None)

    def get_agv_positions(self, warehouse_id):
        """Return the AGV positions for a given warehouse"""
        return self.agv_positions.get(warehouse_id, None)

    def get_slot_statuses(self, warehouse_id):
        """Return the slot statuses for a given warehouse"""
        return self.slot_statuses.get(warehouse_id, None)