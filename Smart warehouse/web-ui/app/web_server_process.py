from web_server import WebServer

WEB_CONFIG_FILE = 'C:/Users/alexa/Desktop/Università/Magistrale/Distributed and IoT/D_Iot_project/V7/web-ui/app/web_conf.yaml'

if __name__ == '__main__':

    # Create Web Server
    web_server = WebServer(WEB_CONFIG_FILE)

    # Run Web Server
    web_server.start()