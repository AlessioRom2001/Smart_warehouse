# Distributed & IoT Warehouse Project

## Overview
This project simulates and manages a smart warehouse using distributed systems and IoT technologies. It features AGV (Automated Guided Vehicle) simulation, slot management, mission scheduling, and a web-based UI for real-time monitoring. The architecture is modular, containerized (Docker), and leverages MQTT for communication between services.

## Main Components
- **AGV Simulator**: Simulates AGVs navigating the warehouse, interacting with sensors and actuators, and executing missions.
- **Warehouse Generator**: Creates the warehouse structure (matrix and graph), including shelves, slots, and AGV start positions.
- **Slot Publisher**: Publishes slot status and updates via MQTT, enabling real-time tracking of slot usage.
- **Mission Publisher**: Schedules and publishes missions for AGVs, integrating path planning and pallet management.
- **Order Generator & Pallet Spawner**: Simulate orders and pallet spawning events in the warehouse.
- **Web UI**: Flask-based interface for visualizing warehouse status, slot usage, AGV telemetry, and configuration parameters.
- **MQTT Broker**: Central message broker for all IoT communications (typically Mosquitto).
- **HTTP API**: RESTful API for inventory and telemetry data, used by the web UI and other services.

## How It Works
1. **Warehouse Initialization**: The warehouse is generated with configurable shelves, columns, levels, and AGVs. The structure is published to MQTT and used by all services.
2. **AGV Simulation**: AGVs receive missions, navigate the warehouse graph, interact with sensors (e.g., ToF, encoders), and update their status.
3. **Slot Management**: Slot Publisher tracks and updates the status of each slot (occupied/free) and publishes changes to MQTT.
4. **Mission Scheduling**: Missions are created and assigned to AGVs, with path planning algorithms ensuring efficient navigation and collision avoidance.
5. **Web Visualization**: The web UI displays a live map of the warehouse, slot status (color-coded), AGV positions, and configuration parameters. Users can monitor and interact with the system in real time.
6. **Order & Pallet Events**: Orders and pallets are generated and managed, triggering AGV missions and slot updates.

## Architecture
- **Microservices**: Each major function runs in its own container (see Dockerfiles and docker-compose.yaml).
- **MQTT Communication**: All real-time data (slots, AGV telemetry, missions) is exchanged via MQTT topics.
- **REST API**: Inventory and telemetry data are exposed via HTTP endpoints for integration and visualization.
- **Web UI**: Connects to the REST API and MQTT broker to provide a user-friendly dashboard.

## MQTT Topic Mapping

Below is a mapping of the main MQTT topics used in the Distributed & IoT Warehouse Project. These topics enable communication between microservices for real-time warehouse management.


| Topic Name                                   | Publisher           | Subscriber(s)         | Payload Description                          |
|----------------------------------------------|---------------------|-----------------------|----------------------------------------------|
| `warehouse/config`                           | warehouse_generator | all services          | Warehouse structure/configuration            |
| `warehouse/config/param/number_of_shelves`   | warehouse_generator | all services          | Number of shelves parameter                  |
| `warehouse/config/param/columns_per_shelf`   | warehouse_generator | all services          | Columns per shelf parameter                  |
| `warehouse/config/param/levels_per_shelf`    | warehouse_generator | all services          | Levels per shelf parameter                   |
| `warehouse/config/param/number_of_agvs`      | warehouse_generator | all services          | Number of AGVs parameter                     |
| `warehouse/config/adjacency_matrix`          | warehouse_generator | all services          | Adjacency matrix of warehouse graph          |
| `warehouse/config/node_positions`            | warehouse_generator | all services          | Node positions in the warehouse              |
| `warehouse/config/node_types`                | warehouse_generator | all services          | Node types (e.g., shelf, AGV start, etc.)    |
| `warehouse/config/agv_start_nodes`           | warehouse_generator | all services          | AGV start node indices                       |
| `warehouse/config/shipping_nodes`            | warehouse_generator | all services          | Shipping node indices                        |
| `warehouse/config/pallet_spawn_nodes`        | warehouse_generator | all services          | Pallet spawn node indices                    |
| `warehouse/config/shelf_nodes`               | warehouse_generator | all services          | Shelf node indices                           |
| `warehouse/config/dimensions`                | warehouse_generator | all services          | Warehouse grid dimensions                    |
| `warehouse/config/graph_stats`               | warehouse_generator | all services          | Graph statistics (nodes, edges, etc.)        |
| `warehouse/config/graph_json`                | warehouse_generator | all services          | NetworkX graph as JSON (nodes, links)        |
| `warehouse/slots/status`                     | slots_publisher     | web-ui, agv_simulator | Slot status updates (occupied/free)          |
| `warehouse/slots/update`                     | slots_publisher     | web-ui, agv_simulator | Slot status change event                     |
| `warehouse/agv/telemetry`                    | agv_simulator       | web-ui, mission_pub   | AGV position, status, telemetry              |
| `warehouse/agv/mission`                      | mission_publisher   | agv_simulator         | Mission assignment and path for AGVs         |
| `warehouse/order/new`                        | order_generator     | mission_publisher     | New order event                              |
| `warehouse/pallet/spawn`                     | pallet_spawner      | mission_publisher     | Pallet spawn event                           |
| `warehouse/mission/status`                   | agv_simulator       | web-ui, mission_pub   | Mission execution status                     |
| `warehouse/telemetry`                        | agv_simulator       | web-ui                | General telemetry data                       |

3. **Access the Web UI**:
   - If running locally: `http://127.0.0.1:7071/storage_view`
   - If running on a server: `http://<server-ip>:7071/storage_view`
4. **Monitor AGVs, slots, and warehouse status** via the web interface.
5. **Interact with the system** by sending orders, spawning pallets, or adjusting warehouse parameters (see simulation and publisher modules).

## Example Workflow
1. Start all containers with Docker Compose.
2. The emulated warehouse is generated and published by running generate_warehouse.py.
3. From the 4 parameters inserted slots_publisher creates the set of storage slots.
3. Whenever the order_generator or the pallet_spawner publish a signal on the broker mission_publisher uses the graph, matrix and node position to create a path to follow and publishes it.
5. Agv_simulator waits for a path published on the topic to start simulating the movement of the AGVs.
4. Slot status and position of the agvs is updated and visualized in the web UI.

Here are the URLs for your web UI:

- **AGV positions:**  
  http://127.0.0.1:7071/agv/AGV_1/position

- **Slot status:**  
  http://127.0.0.1:7071/slots/all
