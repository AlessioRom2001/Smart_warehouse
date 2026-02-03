import time
from random import randint
from sensor import Sensor


class EncoderSensor(Sensor):
    """ Encoder Sensor class, extends Sensor class """

    # Sensor Type
    SENSOR_TYPE: str = "iot.sensor.encoder"
    # Sensor Value Unit
    COORDINATES_UNIT: str = "Coordinates"

    def __init__(self, device_id: str, agv_ref=None):
        """ Initialize the encoder sensor with a devices ID and an initial position """
        super().__init__(device_id, EncoderSensor.SENSOR_TYPE)
        # Initialize the position measurement
        self.value = {
            'x_axis': 0,
            'y_axis': 0,
        }

        # Set the timestamp of the last measurement in milliseconds
        self.timestamp = int(time.time() * 1000)

        # Set the Encoder Unit to Coordinates
        self.unit = EncoderSensor.COORDINATES_UNIT
        
        # Reference to parent AGV to access path
        self.agv_ref = agv_ref

    def update_measurement(self) -> None:
        """ Update the AGV position based on the path followed """

        # If AGV reference exists and has a path, follow it
        if self.agv_ref and self.agv_ref.path and self.agv_ref.graph:
            path = self.agv_ref.path
            graph = self.agv_ref.graph
            
            # Get current position in path
            if self.agv_ref.current_path_index < len(path):
                current_node = path[self.agv_ref.current_path_index]
                
                # Get the actual position from the graph node attributes
                try:
                    node_pos = graph.nodes[current_node].get('pos', None)
                    
                    if node_pos:
                        # node_pos is a tuple (x, y)
                        self.value['x_axis'] = node_pos[0]
                        self.value['y_axis'] = node_pos[1]
                        print(f"AGV {self.agv_ref.device_id} at node {current_node}, position ({self.value['x_axis']:.2f}, {self.value['y_axis']:.2f})")
                    else:
                        # Fallback if position not found in graph
                        print(f"Warning: No position found for node {current_node}, using node ID as coordinate")
                        self.value['x_axis'] = current_node
                        self.value['y_axis'] = current_node
                        
                except (KeyError, AttributeError) as e:
                    print(f"Error accessing node {current_node} position: {e}")
                    self.value['x_axis'] = current_node
                    self.value['y_axis'] = current_node
                
                # Move to next node in path for next update
                self.agv_ref.current_path_index += 1
                
                # If reached end of path, loop back or stay at last position
                if self.agv_ref.current_path_index >= len(path):
                    print(f"AGV {self.agv_ref.device_id} reached end of path")
                    # Option 1: Stay at last position
                    self.agv_ref.current_path_index = len(path) - 1
                    # Option 2: Loop back to start (uncomment if needed)
                    # self.agv_ref.current_path_index = 0
            else:
                # Path exists but we're at or past the end, stay at current position
                print(f"AGV {self.agv_ref.device_id} is at end of path, maintaining position")
        else:
            # No path available or no graph reference, use random coordinates (fallback behavior)
            if self.agv_ref and not self.agv_ref.graph:
                print(f"Warning: AGV {self.agv_ref.device_id} has no graph reference, using random coordinates")
            self.value['x_axis'] = randint(-400, 400)
            self.value['y_axis'] = randint(-400, 400)

        # Set the timestamp of the last measurement in milliseconds
        self.timestamp = int(time.time() * 1000)