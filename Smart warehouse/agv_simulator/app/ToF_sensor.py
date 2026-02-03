import time
from sensor import Sensor
from random import random, gauss
import math


class ToFSensor(Sensor):
    """ ToF sensor class, extends Sensor class implementing the required methods of the base class"""

    # Sensor Type
    SENSOR_TYPE: str = "iot.sensor.tof"
    # Meter unit
    METERS_UNIT: str = "m"
    # Detection threshold (1 meter)
    DETECTION_THRESHOLD: float = 1.0

    def __init__(self, device_id: str, agv_ref=None, initial_distance: float = 1000.0):
        """ Initialize the ToF sensor with a devices ID and an initial distance """
        super().__init__(device_id, ToFSensor.SENSOR_TYPE)

        # Initialize the distance measurement
        self.value = initial_distance
        # Set the timestamp of the last measurement in milliseconds
        self.timestamp = int(time.time() * 1000)

        # Set Unit of Sensor Value
        self.unit = ToFSensor.METERS_UNIT
        
        # Reference to parent AGV
        self.agv_ref = agv_ref
        
        # Detection state
        self.agv_detected = False
        self.closest_agv_id = None
        self.closest_distance = float('inf')

    def update_measurement(self) -> bool:
        """ 
        Update the ToF sensor measurement by checking distance to other AGVs.
        Returns True if another AGV is closer than 1 meter, False otherwise.
        """
        
        # Reset detection state
        self.agv_detected = False
        self.closest_agv_id = None
        self.closest_distance = float('inf')
        self.value = float('inf')
        
        # Check if we have AGV reference and position
        if self.agv_ref:
            my_position = self.agv_ref.get_current_position()
            
            if my_position and self.agv_ref.other_agvs:
                # Check distance to all other AGVs
                for other_agv in self.agv_ref.other_agvs:
                    other_position = other_agv.get_current_position()
                    
                    if other_position:
                        # Calculate Euclidean distance
                        distance = math.sqrt(
                            (my_position[0] - other_position[0])**2 + 
                            (my_position[1] - other_position[1])**2
                        )
                        
                        # Update closest distance
                        if distance < self.closest_distance:
                            self.closest_distance = distance
                            self.closest_agv_id = other_agv.device_id
                            self.value = distance
                
                # Check if any AGV is within detection threshold
                if self.closest_distance < self.DETECTION_THRESHOLD:
                    self.agv_detected = True
                    print(f"⚠️  ToF Alert: AGV {self.agv_ref.device_id} detected {self.closest_agv_id} at {self.closest_distance:.2f}m (< {self.DETECTION_THRESHOLD}m)")
                else:
                    self.value = self.closest_distance if self.closest_distance != float('inf') else 1000.0
            else:
                # No other AGVs or no position available
                self.value = 1000.0
        else:
            # No AGV reference, fallback behavior
            self.value = 1000.0
        
        # Update timestamp
        self.timestamp = int(time.time() * 1000)
        
        return self.agv_detected