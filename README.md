# Distributed & IoT Warehouse Project


## Overview
This project simulates and manages a smart warehouse using distributed systems and IoT technologies. It features AGV simulation, slot management and mission scheduling. The architecture is modular, containerized (Docker), and leverages MQTT for communication between services. It also features an HTTP API inventory for the data visualization through Web-ui.

## Devices Involved

- **AGVs (Automated Guided Vehicles)**: These are mobile robots responsible for transporting pallets from the end of the production line to storage locations within the warehouse. Each AGV is equipped with:
  - **ToF (Time-of-Flight) sensors**: Used to detect obstacles in the AGV's path, ensuring safe navigation.
  - **Wheel encoders**: Allow the AGV to compute its own position by measuring wheel rotations, enabling precise movement and localization.

- **Weight sensors**: Positioned in the pallet pick-up area, these sensors detect the presence of a pallet ready to be collected by an AGV. They provide real-time feedback to the system about pallet availability at the end of the production line.

## Main Components

### Data Inputs
**Warehouse Generator**: <br>
With this module the user can insert the value of 4 parameters to configure the system through a Tkinter user Interface. 
The parameters are values representing: 
  - Number of shelves
  - Number of clomuns per shelf
  - Number of levels per shelf 
  - Number of AGVs

These parameters are deisgned to be easily accesible by the user and at the same time to be easily computable data. <br>
[*generate_warehouse.py*](smart_warehouse\warehouse_generator\generate_warehouse.py) takes the four integers and elaborates them with the logic of the WarehouseMatrix and WarehouseGraph classes respectively from [*matrix.py*](smart_warehouse\warehouse_generator\matrix.py) and [*graph.py*](smart_warehouse\warehouse_generator\graph.py). <br>
The result is the generation of several structures of data that are going to set the base characterization for the computational part of the system.

Data generated:
- Adjecny Matrix
- Node types
- Node positions
- Networkx graph in json

After the configuration values are confirmed, the code gives a visualization of the graph representation of the warehouse in order to let the user check the correct submission of the parameters.

This module also takes the responsability of sending both parameters and configuration data to the MQTT broker publishing them on the `warehouse/config` topic level.

**Order Generator**: <br>
The order generator microservice relies only on [*orders.py*](smart_warehouse\order_generator\app\orders.py) which contains the logic that simulates the arrival of orders to send to the shipping zone.

The algorithm creates a configurable number of orders on a 8h time span and distributed with an exponential randomness by assigning to each the arrival timestamp to construct the json:
```json
{
  "order_id": 1,
  "timestamp": 1707051234
}
```
When the measured timestamp from the start of the service reaches the predicted arrival timestamp it publishes the respective order data to `warehouse/order`.

**Pallet Spawner**: <br>
This module simulates the arrival of pallets from an hypothetical line of production which supplies the warehouse continuously.
The scenario is designed to receive the signal from weight sensors positioned at the end of the line, for this reason [*pallet_spawner.py*](smart_warehouse\pallet_spawner\app\pallet_spawner.py) uses the WeightSensor class to "spawn" a pallet every 10 seconds by publishing on `warehouse/pallet` with a json structure like this:
```json
{
  "pallet_arrived": true,
  "weight": 23.5,
  "unit": "kg",
  "timestamp": 1707051234
}
```

### Data Elaboration

**Slot Publisher**: <br>
The main concer of this module is to create the data of the storage slots that compose the warehouse. <br>
It retrieves the three shelf parameters from the broker to calculate the total number of slots and then it arranges the data for each one of them in a json structure like:
```json
{
  "slot_id": 1,
  "col": 1,
  "row": 2,
  "level": 2,
  "in_use": true
}
```
Finally it publishes them all on warehouse/slots/{slot_id}.

**Mission Publisher**: <br>
The mission publisher microservice works by receiving configuration data from the broker like node position and typeand then generating missions for AGVs. It uses the warehouse Networkx graph and matrix data to compute optimal paths for each mission using Dijkstra algorithm.

The logic is based on listening to the topics `warehouse/order` and `warehouse/pallet` for new events. 
When a new order or pallet arrives, the module uses the PalletScheduler class in [*pallet_scheduler.py*](smart_warehouse\mission_publisher\app\pallet_scheduler.py) to find the closest empty or occupied storage slot depending on which topic the signal arrived. After this  it calculates the best route for for the AGV and generates a mission path in form of set of nodes id.

The mission is then appended in a larger set that stores all the missions and published as MQTT message on the topic `warehouse/missions`.

**AGV Simulator**: <br>

AGV Simulator emulate the robot movement and interaction inside the warehouse. Rather than simply processing incoming data, it acts as a virtual AGV, interpreting mission instructions and autonomously traversing the warehouse graph.

When a new mission arrives on `warehouse/missions`, the simulator decodes the assigned path, republisehs the set of missions without the chosen one and begins routing through the warehouse nodes. [*encoder_sesnor.py*](smart_warehouse\agv_simulator\app\encoder_sensor.py) and [*ToF_sesnor.py*](smart_warehouse\agv_simulator\app\ToF_sensor.py) serve to simulate the function of the sensors mounted on the AGVs which are respctively: measuring the position of the AGV and signalling the presence of obstruating objects. The AGV's internal state evolves in real time, reflecting both its physical location and operational status.

Throughout its operation, the simulator emits telemetry updates to `warehouse/agv/{agv_id}/position`. These messages encapsulate the AGV's id, current position, and a timestamp, for example:
```json
{
  "agv_id": "AGV_1",
  "position": [x, y],
  "timestamp": 1707051234.123
}
```
This continuous data stream enables live monitoring and visualization, allowing other modules to react to AGV progress and warehouse changes as they unfold. Slot status and mission completion are updated automatically as the AGV reaches its goals, providing a realistic simulation of warehouse logistics.

### Communication
**Data fetcher**: Module responsable for the transmission of data between the MQTT broker and the API inventory.
In particular the two data transferred are the agv telemetry and the slots status.
**Web UI**: Flask-based interface for visualizing slot usage and AGV telemetry through web UI interfaces reachable with the two URLs:
- http://127.0.0.1:7071/agv/AGV_1/position (AGV id changable)
- http://127.0.0.1:7071/slots/all

**MQTT Broker**: Central message broker for all IoT communications (typically Mosquitto).

**HTTP API**: RESTful API for inventory, used by the web UI.

### Deployement
- **Docker compose**: Folder of necessary files to perform deployement of the conatiners of the microservices.

## Architecture
- **Microservices**: Each major function runs in its own container (see Dockerfiles and docker-compose.yaml).
- **MQTT Communication**: All real-time data (slots, AGV telemetry, missions) is exchanged via MQTT topics.
- **REST API**: Inventory and telemetry data are exposed via HTTP endpoints for integration and visualization.
- **Web UI**: Connects to the REST API and MQTT broker to provide a user-friendly dashboard.

## Dataflow structure

![](iamges\Smart_warehouse_arch.png)

## How It Works
1. **Warehouse Initialization**: The warehouse is generated with configurable shelves, columns, levels, and AGVs. The structure is published to MQTT and used by all services.
2. **AGV Simulation**: AGVs receive missions, navigate the warehouse graph, interact with sensors (e.g., ToF, encoders), and update their status.
3. **Slot Management**: Slot Publisher tracks and updates the status of each slot (occupied/free) and publishes changes to MQTT.
4. **Mission Scheduling**: Missions are created and assigned to AGVs, with path planning algorithms ensuring efficient navigation and collision avoidance.
5. **Web Visualization**: The web UI displays a live map of the warehouse, slot status (color-coded), AGV positions, and configuration parameters. Users can monitor and interact with the system in real time.
6. **Order & Pallet Events**: Orders and pallets are generated and managed, triggering AGV missions and slot updates.



## MQTT Topic Mapping

Below is a mapping of the main MQTT topics used in the Distributed & IoT Warehouse Project. These topics enable communication between microservices for real-time warehouse management.


| Topic Name                                   | Publisher           | Subscriber(s)         | Payload Description                          | QoS | Retain |
|----------------------------------------------|---------------------|-----------------------|----------------------------------------------|-----|--------|
| `warehouse/config`                           | warehouse_generator | all services          | Warehouse configuration            |  N/D|  N/D   |
| `warehouse/config/param/number_of_shelves`   | warehouse_generator | all services          | Number of shelves parameter                  |  1|  True   |
| `warehouse/config/param/columns_per_shelf`   | warehouse_generator | all services          | Columns per shelf parameter                  |  1|  True   |
| `warehouse/config/param/levels_per_shelf`    | warehouse_generator | all services          | Levels per shelf parameter                   |  1|  True   |
| `warehouse/config/param/number_of_agvs`      | warehouse_generator | all services          | Number of AGVs parameter                     |  1|  True   |
| `warehouse/config/adjacency_matrix`          | warehouse_generator | all services          | Adjacency matrix of warehouse graph          |  1|  Flase   |
| `warehouse/config/node_positions`            | warehouse_generator | all services          | Node positions in the warehouse              |  1|  Flase   |
| `warehouse/config/agv_start_nodes`           | warehouse_generator | all services          | AGV start node indices                       |  1|  False   |
| `warehouse/config/shipping_nodes`            | warehouse_generator | all services          | Shipping node indices                        |  1|  False   |
| `warehouse/config/pallet_spawn_nodes`        | warehouse_generator | all services          | Pallet spawn node indices                    |  1|  False   |
| `warehouse/config/shelf_nodes`               | warehouse_generator | all services          | Shelf node indices                           |  1|  False   |
| `warehouse/config/graph_json`                | warehouse_generator | all services          | NetworkX graph as JSON (nodes, links)        |  1|  False   |
| `warehouse/missions`                     | mission_publisher     | agv_simulator | Set of mission paths          |  1|  False   |
| `warehouse/slots/{slot_id}`                     | slots_publisher     | agv_simulator,data_fetcher | Slot status updates (occupied/free)          |  1|  False   |
| `warehouse/slots/total`                     | slots_publisher     | agv_simulator | Total number of slots         |  1|  False   |
| `warehouse/agv/{agv_id}/position`                      | agv_simulator   | data_fetcher         |   AGV position       |  0|  False   |
| `warehouse/order`                        | order_generator     | mission_publisher     | New order event                              |  1|  False   |
| `warehouse/pallet`                     | pallet_spawner      | mission_publisher     | Pallet spawn event                           |  1|  False   |

## Example Workflow
1. Start all containers with Docker Compose.
2. The emulated warehouse is generated and published by running generate_warehouse.py.
3. From the 4 parameters inserted slots_publisher creates the set of storage slots.
3. Whenever the order_generator or the pallet_spawner publish a signal on the broker mission_publisher uses the graph, matrix and node position to create a path to follow and publishes it.
5. Agv_simulator waits for a path published on the topic to start simulating the movement of the AGVs.
4. Slot status and position of the agvs is updated and visualized in the web UI.