import requests
from flask import Flask, request, render_template
import os
import yaml
import threading


class WebServer:

    def __init__(self, config_file:str):

        # Server Thread
        self.server_thread = None

        # Save the configuration file
        self.config_file = config_file

        # Get the main communication directory
        main_app_path = ""

        # Construct the file path
        template_dir = os.path.join(main_app_path, 'templates')

        # Set a default configuration
        self.configuration_dict = {
            "web": {
                "host": "0.0.0.0",
                "port": 7071,
                "api_base_url": "http://127.0.0.1:7070/api/v1/iot/inventory"
            }
        }

        # Read Configuration from target Configuration File Path
        self.read_configuration_file()

        # Create the Flask app
        self.app = Flask(__name__, template_folder=template_dir)

        # Add URL rules to the Flask app mapping the URL to the function
        self.app.add_url_rule('/warehouse/config/parameters', 'warehouse_parameters', self.warehouse_parameters)
        self.app.add_url_rule('/agv/<agv_id>/position', 'agv_position', self.agv_position)
        self.app.add_url_rule('/slots/all', 'all_slots', self.all_slots)
        self.app.add_url_rule('/storage_view', 'storage_view', self.storage_view)

    def read_configuration_file(self):
        """ Read Configuration File for the Web Server
         :return:
        """

        # Get the main communication directory
        main_app_path = ""

        # Construct the file path
        file_path = os.path.join(main_app_path, self.config_file)

        with open(file_path, 'r') as file:
            self.configuration_dict = yaml.safe_load(file)

        print("Read Configuration from file ({}): {}".format(self.config_file, self.configuration_dict))

    def warehouse_parameters(self):
        # Recupera entrambi i parametri
        shelves = self.http_get_number_of_shelves()
        columns = self.http_get_columns_per_shelf()
        levels = self.http_get_levels_per_shelf()
        agvs = self.http_get_number_of_agvs()
        parameters = {
            "number_of_shelves": shelves.get("value"),
            "columns_per_shelf": columns.get("value"),
            "levels_per_shelf": levels.get("value"),
            "number_of_agvs": agvs.get("value")
        }
        print("DEBUG parameters:", parameters)
        return render_template('warehouse_parameters.html', parameters=parameters)

    def http_get_number_of_shelves(self):
        """ Get all locations from the remote server over HTTP"""

        # Get the base URL from the configuration
        base_http_url = self.configuration_dict['web']['api_base_url']
        target_url = f'{base_http_url}/warehouse/config/parameters/number_of_shelves'

        # Send the GET request
        response_string = requests.get(target_url)

        # Return the JSON response
        return response_string.json()

    def http_get_columns_per_shelf(self):
        """ Get all locations from the remote server over HTTP"""

        # Get the base URL from the configuration
        base_http_url = self.configuration_dict['web']['api_base_url']
        target_url = f'{base_http_url}/warehouse/config/parameters/columns_per_shelf'

        # Send the GET request
        response_string = requests.get(target_url)

        # Return the JSON response
        return response_string.json()
    
    def http_get_levels_per_shelf(self):
        """ Get all locations from the remote server over HTTP"""

        # Get the base URL from the configuration
        base_http_url = self.configuration_dict['web']['api_base_url']
        target_url = f'{base_http_url}/warehouse/config/parameters/levels_per_shelf'

        # Send the GET request
        response_string = requests.get(target_url)

        # Return the JSON response
        return response_string.json()
    
    def http_get_number_of_agvs(self):
        """ Get all locations from the remote server over HTTP"""

        # Get the base URL from the configuration
        base_http_url = self.configuration_dict['web']['api_base_url']
        target_url = f'{base_http_url}/warehouse/config/parameters/number_of_agvs'

        # Send the GET request
        response_string = requests.get(target_url)

        # Return the JSON response
        return response_string.json()

    def http_get_agv_position(self, agv_id):
        """Get AGV position from the remote server over HTTP"""
        base_http_url = self.configuration_dict['web']['api_base_url']
        target_url = f'{base_http_url}/warehouse/config/parameters/agv/{agv_id}/position'
        response = requests.get(target_url)
        return response.json()

    def agv_position(self, agv_id=None):
        # Se agv_id è passato, mostra solo quell'AGV, altrimenti mostra tutti (se vuoi estendere)
        agv_positions = {}
        if agv_id:
            agv_data = self.http_get_agv_position(agv_id)
            if agv_data and 'position' in agv_data:
                agv_positions[agv_id] = agv_data
        # In futuro puoi aggiungere qui la logica per più AGV
        return render_template('agv_telemetry.html', agv_positions=agv_positions)

    def all_slots(self):
        base_http_url = self.configuration_dict['web']['api_base_url']
        target_url = f'{base_http_url}/warehouse/config/parameters/slots'
        response = requests.get(target_url)
        print("DEBUG all_slots response:", response.status_code)
        slots_json = response.json()
        slots_list = slots_json.get("slots", [])
        return render_template('slot_status.html', slots=slots_list)
    
    def storage_view(self):
        # Recupera i parametri di configurazione della warehouse
        shelves = self.http_get_number_of_shelves()
        columns = self.http_get_columns_per_shelf()
        levels = self.http_get_levels_per_shelf()
        parameters = {
            "number_of_shelves": shelves.get("value"),
            "columns_per_shelf": columns.get("value"),
            "levels_per_shelf": levels.get("value")
        }
        # Recupera lo stato degli slot
        base_http_url = self.configuration_dict['web']['api_base_url']
        target_url = f'{base_http_url}/warehouse/config/parameters/slots'
        response = requests.get(target_url)
        print("DEBUG all_slots response:", response.status_code)
        slots_json = response.json()
        slots_list = slots_json.get("slots", [])
        return render_template('storage_view.html', slots=slots_list, parameters=parameters)

    def run_server(self):
        """ Run the Flask Web Server"""
        self.app.run(host=self.configuration_dict['web']['host'], port=self.configuration_dict['web']['port'])

    def start(self):
        self.server_thread = threading.Thread(target=self.run_server)
        self.server_thread.start()

    def stop(self):
        """ Stop the REST API Server (Flask Method)
        In this code, request.environ.get('werkzeug.server.shutdown')
        retrieves the shutdown function from the environment.
        If the function is not found, it raises a RuntimeError,
        indicating that the server is not running with Werkzeug.
        If the function is found, it is called to shut down the server."""

        # Shutdown the server
        func = request.environ.get('werkzeug.server.shutdown')
        if func is None:
            raise RuntimeError('Not running with the Werkzeug Server')

        # Call the shutdown function
        func()

        # Wait for the server thread to join
        self.server_thread.join()