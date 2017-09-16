# Api.ai - sample webhook implementation in Python for IOAnt platform
This python application is a boilerplate for webhook api.ai fulfillments to IOAnt platform

## Set up
Install requirements:
```sh
# It is recommended that you create a virtual environment
pip install -r requirements.txt
```

Set up configuration.json:
```sh
# copy the configuration template file
cp configuration_default.json configuration.json
```

Contents of configuration.json
```json
{
    "ioant" : {
        "mqtt" : {
            "global" : "global_topic",
            "local" : "local_topic",
            "client_id" : "api",
            "broker" : "ioant.com",
            "user" : "",
            "password" : "",
            "port" : 1883
        },
        "web_server" : {
            "port": 5000
        },
        "communication_delay" : 5000,
        "latitude" : 0.0,
        "longitude" : 0.0,
        "app_generic_a" : 0,
        "app_generic_b" : 0,
        "app_generic_c" : 0
    },
    "app_name" : "API AI IOAnt Bot"
}
```

## Run the application
The webserver will liste on **0.0.0.0:[port]/webhook**

Start the application by running:
```
python main.py
```
