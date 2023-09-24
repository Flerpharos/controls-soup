#!/usr/bin/env python

from yaml import load, Loader
from controls import controls, moveTo, constrained_angle
from gpiozero.pins.rpigpio import RPiGPIOFactory
from gpiozero import MCP3008, Button, Device
from gpiozero.tools import quantized
from time import sleep

# Use Rpi.GPIO
Device.pin_factory = RPiGPIOFactory()

with open("confg.yaml", "r") as confg:
    config = load(confg, Loader=Loader)["inputs"]

button = Button(config["button"])
vel = config["vel"]

SELECT_CHANGE_SLEEP_TIME = 0.3  # seconds
LOOP_SLEEP_TIME = 0.2  # seconds

# TODO set default angles to move towards
# TODO add joint reversibility in controls.py

if config["type"] == "disable":
    pass
if config["type"] == "select":
    select = quantized(MCP3008(config["select"]), 3)
    main = MCP3008(config["main"])

    axes = ["z", "y", "x"]
    axis = 0

    position = {"x": 0, "y": 0, "z": 0}

    button.when_activated = lambda: controls["finger"].forward()
    button.when_deactivated = lambda: controls["finger"].backward()

    while True:
        selector = next(select)
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

    button.when_activated = lambda: controls["finger"].forward()
    button.when_deactivated = lambda: controls["finger"].backward()

    base = controls["base"]
    arm = controls["arm"]
    forearm = controls["forearm"]

    while True:
        X = next(x)
        Y = next(y)
        Z = next(z)

        if X < 0.5:
            base.angle = constrained_angle(base, base.angle - vel)
        elif X > 0.5:
            base.angle = constrained_angle(base, base.angle + vel)

        if Y < 0.5:
            arm.angle = constrained_angle(arm, arm.angle - vel)
            forearm.angle = constrained_angle(forearm, forearm.angle + 2 * vel)
        elif Y > 0.5:
            arm.angle = constrained_angle(arm, arm.angle + vel)
            forearm.angle = constrained_angle(forearm, forearm.angle - 2 * vel)

        if Z < 0.5:
            arm.angle = constrained_angle(arm, arm.angle - vel)
            forearm.angle = constrained_angle(forearm, forearm.angle - vel)
        elif Z > 0.5:
            arm.angle = constrained_angle(arm, arm.angle + vel)
            forearm.angle = constrained_angle(forearm, forearm.angle + vel)

        sleep(LOOP_SLEEP_TIME)
elif config["type"] == "ik":
    x = MCP3008(config["x"])
    y = MCP3008(config["y"])
    z = MCP3008(config["z"])

    position = {"x": 0, "y": 0, "z": 0}

    button.when_activated = lambda: controls["finger"].forward()
    button.when_deactivated = lambda: controls["finger"].backward()

    while True:
        position["x"] += vel * (x.value - 0.5)
        position["y"] += vel * (y.value - 0.5)
        position["z"] += vel * (z.value - 0.5)
        moveTo(position["x"], position["y"], position["z"])

        sleep(LOOP_SLEEP_TIME)
elif config["type"] == "jointed":
    first = MCP3008(config["first"])
    second = MCP3008(config["second"])

    JOINTED_AXES = ["base", "arm", "actuator", "forearm"]
    JOINT_TYPES = ["servo", "servo", "motor", "servo"]
    index = 0

    def switch_index():
        global index
        index = (index + 2) % len(JOINTED_AXES)
        sleep(SELECT_CHANGE_SLEEP_TIME)

    def control_joint(control, control_type, value):
        if control_type == "servo":
            control.angle = constrained_angle(control, control.angle + vel * value)
            return

        if value < -0.1:
            control.backward()
        elif value > 0.1:
            control.forward()

    button.when_activated = switch_index

    while True:
        First = first.value - 0.5
        Second = second.value - 0.5

        first_control = controls[JOINTED_AXES[index]]
        first_type = JOINT_TYPES[index]

        if index + 1 < len(JOINTED_AXES):
            second_control = controls[JOINTED_AXES[index + 1]]
            second_type = JOINT_TYPES[index + 1]
        else:
            second_control = None
            second_type = None

        control_joint(first_control, first_type, First)

        if second_type is not None:
            control_joint(second_control, second_type, Second)

        sleep(LOOP_SLEEP_TIME)
else:
    raise NotImplementedError(
        f"Control type {config['type']} is not available. "
        + "Choose disable, select, positional, jointed, or ik"
    )
