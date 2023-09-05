#!/usr/bin/env python

from yaml import load, Loader
from controls import controls, moveTo
from gpiozero.pins.rpigpio import RPiGPIOFactory
from gpiozero import MCP3008, Button, Device
from gpiozero.tools import quantized
from time import sleep

# Use Rpi.GPIO
Device.pin_factory = RPiGPIOFactory()

with open("confg.yaml", "r") as confg:
    config = load(confg, Loader=Loader)["inputs"]

button = Button(config["button"])

SELECT_CHANGE_SLEEP_TIME = 0.3  # seconds
LOOP_SLEEP_TIME = 0.2  # seconds

if config["type"] == "select":
    select = quantized(MCP3008(config["select"]), 3)
    main = MCP3008(config["main"])
    vel = config["vel"]

    axes = ["z", "y", "x"]
    axis = 0

    position = {"x": 0, "y": 0, "z": 0}

    while True:
        selector = select()
        if selector < 0.5:
            axis = (axis - 1) % len(axes)
            sleep(SELECT_CHANGE_SLEEP_TIME)
        elif selector > 0.5:
            axis = (axis + 1) % len(axes)
            sleep(SELECT_CHANGE_SLEEP_TIME)

        position[axes[axis]] += vel * (main.value - 0.5)
        moveTo(position["x"], position["y"], position["z"])

        sleep(LOOP_SLEEP_TIME)

elif config["type"] == "positional":
    x = quantized(MCP3008(config["x"]), 3)
    y = quantized(MCP3008(config["y"]), 3)
    z = quantized(MCP3008(config["z"]), 3)
    vel = config["vel"]

    while True:
        X = x()
        Y = y()
        Z = z()

        if X < 0.5:
            controls["base"].angle -= vel
        elif X > 0.5:
            controls["base"].angle += vel

        if Y < 0.5:
            controls["arm"].angle -= vel
            controls["forearm"].angle += 2 * vel
        elif Y > 0.5:
            controls["arm"].angle += vel
            controls["forearm"].angle -= 2 * vel

        if Z < 0.5:
            controls["arm"].angle -= vel
            controls["forearm"].angle -= vel
        elif Z > 0.5:
            controls["arm"].angle += vel
            controls["forearm"].angle += vel

        sleep(LOOP_SLEEP_TIME)
elif config["type"] == "ik":
    x = MCP3008(config["x"])
    y = MCP3008(config["y"])
    z = MCP3008(config["z"])
    vel = config["vel"]

    position = {"x": 0, "y": 0, "z": 0}

    while True:
        position["x"] += vel * (x.value - 0.5)
        position["y"] += vel * (y.value - 0.5)
        position["z"] += vel * (z.value - 0.5)
        moveTo(position["x"], position["y"], position["z"])

        sleep(LOOP_SLEEP_TIME)
else:
    raise NotImplementedError(
        f"Control type {config['type']} is not available. "
        + "Choose select, positional, or ik"
    )
