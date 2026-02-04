# MQTT Broker - Eclipse Mosquitto

This setup provides an MQTT broker using Eclipse Mosquitto with Docker.

## Configuration

- **Image**: `eclipse-mosquitto:2.0.12` (official Docker Hub image)
- **Port**: 1883 (MQTT default)
- **Persistence**: Enabled with local data folder
- **Logs**: Stored in local log folder

## Volume Mappings

- `./mosquitto.conf` → `/mosquitto/config/mosquitto.conf` (Configuration file)
- `./mosquitto/data` → `/mosquitto/data` (Persistence data)
- `./mosquitto/log` → `/mosquitto/log` (Log files)

## Quick Start

### Using Docker Compose (Recommended)

```bash
cd mqtt-broker
docker-compose up -d
```

### Using Docker CLI

```bash
docker run -d \
  --name mqtt-broker \
  --restart always \
  -p 1883:1883 \
  -v "$(pwd)/mosquitto.conf:/mosquitto/config/mosquitto.conf" \
  -v "$(pwd)/mosquitto/data:/mosquitto/data" \
  -v "$(pwd)/mosquitto/log:/mosquitto/log" \
  eclipse-mosquitto:2.0.12
```

### For Windows (PowerShell)

```powershell
docker run -d `
  --name mqtt-broker `
  --restart always `
  -p 1883:1883 `
  -v "${PWD}/mosquitto.conf:/mosquitto/config/mosquitto.conf" `
  -v "${PWD}/mosquitto/data:/mosquitto/data" `
  -v "${PWD}/mosquitto/log:/mosquitto/log" `
  eclipse-mosquitto:2.0.12
```

## Management Commands

### Stop the broker
```bash
docker-compose down
```

### View logs
```bash
docker-compose logs -f mosquitto
```

### Restart the broker
```bash
docker-compose restart
```

## Testing the Broker

### Subscribe to a topic
```bash
docker exec -it mqtt-broker mosquitto_sub -h localhost -t test/topic
```

### Publish a message
```bash
docker exec -it mqtt-broker mosquitto_pub -h localhost -t test/topic -m "Hello MQTT"
```

## Security Note

This configuration allows anonymous connections. For production use, configure authentication by:
1. Setting `allow_anonymous false` in [mosquitto.conf](mosquitto.conf)
2. Creating a password file with `mosquitto_passwd`
3. Adding `password_file /mosquitto/config/passwd` to the configuration
