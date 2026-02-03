import time
from sensor import Sensor
from random import random, gauss
import math


class WeightSensor(Sensor):
    """ Weight sensor class, extends Sensor class implementing the required methods of the base class"""

    # Sensor Type
    SENSOR_TYPE: str = "iot.sensor.weight"
    # Kilogram unit
    KILOGRAM_UNIT: str = "kg"

    def __init__(self, device_id: str, pallet_weight: int = 0):
        """ Initialize the weight sensor with a devices ID and an initial weight """
        super().__init__(device_id, WeightSensor.SENSOR_TYPE)

        # Initialize the weight measurement
        self.value = pallet_weight
        # Set the timestamp of the last measurement in milliseconds
        self.timestamp = int(time.time() * 1000)

        # Set Unit of Sensor Value
        self.unit = WeightSensor.KILOGRAM_UNIT

    def update_measurement(self) -> None:
        """ Record that a pallet is present at this timestamp """
        
        # Mark that a pallet is present
        self.is_there_a_pallet = True
        
        # Assign a random weight between 35 and 50 kg using Gaussian distribution
        self.value = max(35, min(50, gauss(42.5, 2.5)))
        
        # Update timestamp
        self.timestamp = int(time.time() * 1000)