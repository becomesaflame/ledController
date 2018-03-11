#!/usr/bin/env python3

"""An MQTT connected power outlet controller"""
import json
import logging
import paho.mqtt.client as mqtt
import rgbled
import RPi.GPIO as gpio
import sys
import time

def setupGPIO(leds):
    """Sets up GPIO pins"""

    # Use Raspberry Pi board pin numbers
    gpio.setmode(gpio.BOARD)

    # set up the GPIO pins
    gpio.setup(leds.get("red_pin"), gpio.OUT)
    gpio.setup(leds.get("green_pin"), gpio.OUT)
    gpio.setup(leds.get("blue_pin"), gpio.OUT)


def on_message(client, userdata, message):
    """Callback function for subscriber"""

    payload = str(message.payload.decode("utf-8"))
    state_topic = userdata.get("state_topic")
    pin = userdata.get("gpio_pin")

    if (payload == "ON"):
        client.publish(state_topic, "ON")
        logging.debug("State: Publishing ON to %s", state_topic)
        gpio.output(pin, gpio.HIGH)
        inPin = gpio.input(5) # debug
        logging.info("Turning ON")
        logging.debug("Outputting %d", inPin)
    if (payload == "OFF"):
        client.publish(state_topic, "OFF")
        logging.debug("State: Publishing OFF to %s", state_topic)
        gpio.output(pin, gpio.LOW)
        inPin = gpio.input(5) # debug
        logging.info("Turning OFF")
        logging.debug("Outputting %d", inPin)

    logging.debug("message payload %s", payload)
    logging.debug("message topic=%s",message.topic)
    logging.debug("message qos=%s",message.qos)
    logging.debug("message retain flag=%s",message.retain)
    logging.debug("userdata: %s", repr(userdata))

def listen(mqtt_cfg):
    """Listen on an MQTT topic"""
    logging.info("Setting up MQTT %s", repr(mqtt_cfg))

    command_topic = mqtt_cfg.get("command_topic")
    state_topic = mqtt_cfg.get("state_topic")
    availability_topic = mqtt_cfg.get("availability_topic")

    mqttc = mqtt.Client(userdata=mqtt_cfg)

    # Attach function to callback
    mqttc.on_message=on_message 
    
    if username:
        mqttc.username_pw_set(username, password)
    
    mqttc.connect(host, port)
    mqttc.loop_start()
    mqttc.subscribe(command_topic)


    # Tell server that we're available
    mqttc.publish(availability_topic, "ON", retain=True)
    logging.debug("Available: Publishing ON to %s", availability_topic)


def main(config_path):
    """main entry point, load and validate config and call generate"""
    time.sleep(30) # wait for network after boot
    try:
        with open(config_path) as handle:
            logging.basicConfig(filename='powerPi.log', filemode='w', level=logging.DEBUG)
            logging.info("Powering up\npowerPi v0.0\n%s\n\n", time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))

            config = json.load(handle)

            # Set up RPi GPIO pin
            leds = config.get("leds")
            setupGPIO(leds)
            led_strip = rgbled.rgbled(leds.get("red_pin"), leds.get("green_pin"), leds.get("blue_pin"))

            # Set up MQTT
            mqtt_cfg = config.get("mqtt", {})
            listen(mqtt_cfg)

            while(1):
                time.sleep(5)

            # generate(host, port, username, password, topic, sensors, interval_ms, verbose)
    except IOError as error:
        print("Error opening config file '%s'" % config_path, error)

if __name__ == '__main__':
    if len(sys.argv) == 2:
        main(sys.argv[1])
    else:
        print("usage %s config.json" % sys.argv[0])
