import time
import json
from weight_sensor import WeightSensor
import paho.mqtt.client as mqtt
import threading


class PalletSpawner:
    """Simulates pallet arrivals by publishing to MQTT broker"""

    def __init__(self, broker_address: str = "my-mosquitto-broker", broker_port: int = 1883):
        """Initialize the pallet spawner with broker connection details"""
        self.broker_address = broker_address
        self.broker_port = broker_port
        self.topic = "warehouse/pallet"
        
        # Create MQTT client
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        
        # Create weight sensor instance
        self.weight_sensor = WeightSensor(device_id="weight_sensor_01")
        
    def on_connect(self, client, userdata, flags, rc):
        """Callback for when client connects to broker"""
        if rc == 0:
            print(f"Connected to MQTT broker at {self.broker_address}:{self.broker_port}")
        else:
            print(f"Failed to connect, return code {rc}")
    
    def simulate_pallet_arrival(self):
        """Simulate a pallet arrival and publish to broker"""
        # Update weight sensor measurement
        self.weight_sensor.update_measurement()
        
        # Create payload
        payload = {
            "pallet_arrived": True,
            "weight": self.weight_sensor.value,
            "unit": self.weight_sensor.unit,
            "timestamp": self.weight_sensor.timestamp
        }
        
        # Publish to broker
        result = self.client.publish(self.topic, json.dumps(payload), qos=1, retain=False)
        
        if result.rc == mqtt.MQTT_ERR_SUCCESS:
            print(f"Published pallet arrival: {payload}")
        else:
            print(f"Failed to publish message")
    
    def start(self):
        """Start the pallet spawner simulation"""
        # Wait for config before starting
        wait_for_config(self.broker_address, self.broker_port, CONFIG_TOPIC)
        # Connect to broker
        self.client.connect(self.broker_address, self.broker_port, 60)
        self.client.loop_start()
        
        print("Pallet spawner started. Publishing every 10 seconds...")
        
        try:
            while True:
                self.simulate_pallet_arrival()
                time.sleep(10)
        except KeyboardInterrupt:
            print("\nStopping pallet spawner...")
            self.client.loop_stop()
            self.client.disconnect()


CONFIG_TOPIC = "warehouse/config/param/number_of_shelves"
config_received_event = threading.Event()

def on_config_message(client, userdata, msg):
    print(f"Received config message on {CONFIG_TOPIC}: {msg.payload.decode()}")
    config_received_event.set()


def wait_for_config(broker="my-mosquitto-broker", port=1883, config_topic=CONFIG_TOPIC):
    client = mqtt.Client()
    client.on_message = on_config_message
    client.connect(broker, port, 60)
    client.subscribe(config_topic)
    client.loop_start()
    print(f"Waiting for configuration on topic {config_topic}...")
    config_received_event.wait()  # Block until event is set
    client.loop_stop()
    client.disconnect()
    print("Configuration received. Proceeding with pallet spawning.")


if __name__ == "__main__":
    spawner = PalletSpawner()
    spawner.start()