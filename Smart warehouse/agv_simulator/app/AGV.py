from ToF_sensor import ToFSensor
from device import Device
from encoder_sensor import EncoderSensor
from switch import Switch
import json
import paho.mqtt.client as mqtt
import time


class AGV(Device):
    """ AGV class, extends Device Class and add new features, attributes and methods """

    # Device Type
    DEVICE_TYPE: str = "iot.AGV"

    def __init__(self, device_id: str, encoder_sensor_number: int = 2, broker_ip: str = "127.0.0.1", broker_port: int = 1883, graph=None, node_positions=None):
        """ Initialize the device with the devices ID and type"""
        super().__init__(device_id, AGV.DEVICE_TYPE)

        # MQTT Configuration
        self.broker_ip = broker_ip
        self.broker_port = broker_port
        self.path = None
        self.path_received = False
        self.current_path_index = 0
        
        # Store reference to the warehouse graph for position lookup
        self.graph = graph
        # Store reference to node positions (dict node_id: (x, y))
        self.node_positions = node_positions
        
        # List of other AGVs in the system for collision detection
        self.other_agvs = []

        # Declare and initialize the AGV ToF Sensor with reference to this AGV
        self.ToF_sensor = ToFSensor(f'{self.device_id}_ToF_Sensor', self)

        # Declare and initialize the AGV Switch Actuator
        self.switch = Switch(f'{self.device_id}_switch')

        # Declare and initialize the list to store machine's encoder sensors
        self.encoder_sensor_list = []
        
        # Initialize encoder sensors based of the parameter passed in the constructor (default = 2)
        for sensor_index in range(encoder_sensor_number):
            self.encoder_sensor_list.append(EncoderSensor(f'{self.device_id}_encoder_{sensor_index}', self))

    def update_measurements(self) -> None:
        """Update all the measurements for the sensors associated to the Machine (energy and accelerometer)
        Usa node_positions se disponibili per aggiornare la posizione."""
        self.ToF_sensor.update_measurement()
        for encoder_sensor in self.encoder_sensor_list:
            if self.node_positions is not None and self.path and self.current_path_index < len(self.path):
                current_node = self.path[self.current_path_index]
                pos = self.node_positions.get(current_node)
                if pos:
                    encoder_sensor.value['x_axis'] = pos[0]
                    encoder_sensor.value['y_axis'] = pos[1]
                    print(f"AGV {self.device_id} at node {current_node}, position {pos}")
                else:
                    encoder_sensor.value['x_axis'] = current_node
                    encoder_sensor.value['y_axis'] = current_node
                    print(f"AGV {self.device_id} at node {current_node}, no position found, using node id")
                self.current_path_index += 1
                if self.current_path_index >= len(self.path):
                    self.current_path_index = len(self.path) - 1
            else:
                encoder_sensor.update_measurement()
    
    def get_current_position(self):
        """Get the current position of the AGV from the first encoder sensor"""
        if self.encoder_sensor_list:
            return (self.encoder_sensor_list[0].value['x_axis'], 
                    self.encoder_sensor_list[0].value['y_axis'])
        return None
    
    def set_other_agvs(self, agv_list):
        """Set the list of other AGVs in the system for collision detection"""
        # Filter out this AGV from the list
        self.other_agvs = [agv for agv in agv_list if agv.device_id != self.device_id]

    def get_json_description(self) -> str:
        """Return the list of last values for each device of the AGV
        This implementation is custom with respect to the default implementation in the Device class
        since it includes the list of encoder sensors, ToF sensor, actuators and the machine information"""

        encoder_description_list = []

        # For each encoder sensor update the device descriptions and measurements
        for encoder_sensor in self.encoder_sensor_list:
            encoder_description_list.append(encoder_sensor.get_json_description())

        result_dict = {
            "machine_id": self.device_id,
            "machine_type": self.device_type,
            "switch_id": self.switch.get_json_description(),
            "ToF_sensor_id": self.ToF_sensor.get_json_description(),
            "encoder_sensor_id_list": encoder_description_list
        }

        return json.dumps(result_dict)

    def get_json_measurement(self) -> str:
        """Return the list of last values for each device of the AGV
        This implementation is custom with respect to the default implementation in base class
        since it includes the measurements of encoder sensors, ToF sensor, actuators and the machine information"""

        encoder_description_list = []
        # For each encoder sensor update the device descriptions and measurements
        for encoder_sensor in self.encoder_sensor_list:
            # I need to convert the JSON string to a dictionary in order to avoid nested JSON objects
            dict_enc = json.loads(encoder_sensor.get_json_measurement())
            encoder_description_list.append(dict_enc)

        # I need to convert the JSON string to a dictionary in order to avoid nested JSON objects
        # for the switch and ToF sensor

        switch_measurement_dict = json.loads(self.switch.get_json_measurement())
        ToF_sensor_measurement_dict = json.loads(self.ToF_sensor.get_json_measurement())

        result_dict = {
            "machine_id": self.device_id,
            "switch": switch_measurement_dict,
            "ToF_sensor": ToF_sensor_measurement_dict,
            "encoder_sensor_list": encoder_description_list
        }

        return json.dumps(result_dict)
    
    def get_path(self, topic: str = None, timeout: int = 30) -> list:
        """ 
        Get the first path published on the MQTT broker queue.
        
        Args:
            topic: MQTT topic to subscribe to (default: "agv/{device_id}/path")
            timeout: Maximum time to wait for a path in seconds (default: 30)
            
        Returns:
            list: The path received from the broker, or None if timeout
        """
        # Use default topic if not provided
        if topic is None:
            topic = f"agv/{self.device_id}/path"
        
        # Reset path state
        self.path = None
        self.path_received = False
        
        # Callback when connected to broker
        def on_connect(client, userdata, flags, rc):
            if rc == 0:
                print(f"AGV {self.device_id} connected to MQTT Broker")
                client.subscribe(topic)
                print(f"AGV {self.device_id} subscribed to topic: {topic}")
            else:
                print(f"AGV {self.device_id} failed to connect, return code {rc}")
        
        # Callback when message is received
        def on_message(client, userdata, msg):
            try:
                # Parse the received path
                payload = json.loads(msg.payload.decode())
                self.path = payload.get("path", [])
                self.path_received = True
                print(f"AGV {self.device_id} received path: {self.path}")
            except json.JSONDecodeError as e:
                print(f"Error decoding JSON: {e}")
            except Exception as e:
                print(f"Error processing message: {e}")
        
        # Create MQTT client
        client_id = f"{self.device_id}_path_subscriber"
        mqtt_client = mqtt.Client(client_id)
        mqtt_client.on_connect = on_connect
        mqtt_client.on_message = on_message
        
        try:
            # Connect to broker
            mqtt_client.connect(self.broker_ip, self.broker_port, 60)
            mqtt_client.loop_start()
            
            # Wait for path with timeout
            start_time = time.time()
            while not self.path_received and (time.time() - start_time) < timeout:
                time.sleep(0.1)
            
            # Stop the loop and disconnect
            mqtt_client.loop_stop()
            mqtt_client.disconnect()
            
            if self.path_received:
                print(f"AGV {self.device_id} successfully retrieved path")
                self.current_path_index = 0  # Reset path index when new path is received
                return self.path
            else:
                print(f"AGV {self.device_id} timeout waiting for path")
                return None
                
        except Exception as e:
            print(f"Error connecting to MQTT broker: {e}")
            mqtt_client.loop_stop()
            mqtt_client.disconnect()
            return None

    def start(self) -> None:
        """ Start machine operations setting the actuator to ON and updating a sample of available sensors"""

        # Turn ON the switch
        self.switch.invoke_action(Switch.ACTION_TYPE_SWITCH, Switch.STATUS_ON)

        # Update Machine Measurements
        self.update_measurements()

    def stop(self) -> None:
        """ Stop machine operations setting the actuator to OFF and updating a sample of available sensors"""

        # Update Sensor Measurements
        self.update_measurements()

        # Turn OFF the switch
        self.switch.invoke_action(Switch.ACTION_TYPE_SWITCH, Switch.STATUS_OFF)