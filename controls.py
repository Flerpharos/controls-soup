from yaml import load, Loader
from gpiozero import Device, AngularServo, Motor
from gpiozero.pins.mock import MockFactory, MockPWMPin
from tinyik import Actuator, visualize
import numpy as np

if __name__ == "__main__":
    Device.pin_factory = MockFactory(pin_class=MockPWMPin)

with open("confg.yaml", "r") as confg:
    config = load(confg, Loader=Loader)

# import me to get specific controls
controls = {}

for name, values in config["controls"].items():
    if "type" not in values:
        raise KeyError(f"Required item 'type' not found for control {name}")

    if values["type"] == "servo":  # handle servo init
        controls[name] = AngularServo(
            values["pin"],
            min_pulse_width=values["pulse"]["min"] / 1000,
            max_pulse_width=values["pulse"]["max"] / 1000,
            min_angle=values["range"] / -2,
            max_angle=values["range"] / 2,
        )
    elif values["type"] == "actuator":  # handle actuator init
        controls[name] = Motor(values["pins"]["hi"], values["pins"]["lo"], pwm=False)
    else:
        raise NotImplementedError(
            f"Control type {values['type']} binding not implemented"
        )


def getRotationMatrix(theta, psi, phi):
    return np.array(
        [
            [
                np.cos(theta) * np.cos(psi) + np.sin(theta) * np.sin(phi) * np.sin(psi),
                -np.cos(theta) * np.sin(psi)
                + np.cos(psi) * np.sin(theta) * np.sin(psi),
                np.cos(phi) * np.sin(theta),
            ],
            [np.cos(phi) * np.sin(psi), np.cos(phi) * np.cos(psi), -np.sin(phi)],
            [
                -np.cos(psi) * np.sin(theta)
                + np.cos(theta) * np.sin(phi) * np.sin(psi),
                np.sin(theta) * np.sin(psi)
                + np.cos(theta) * np.cos(psi) * np.sin(theta),
                np.cos(theta) * np.cos(phi),
            ],
        ]
    )


# DO NOT IMPORT
controlIndices = []
ik_params = []
frame = {"x": 0, "y": 0, "z": 0}  # radians

for value in config["ik"]:
    if "control" in value:
        name = value["control"]
        axis = value["axis"]
        base = np.deg2rad(value["angle"])

        if base != 0:
            frame["x"] += base if axis == "x" else 0
            frame["y"] += base if axis == "y" else 0
            frame["z"] += base if axis == "z" else 0

        controlIndices.append(name)
        ik_params.append(axis)
    else:
        # this is untested, it's probably better to leave all 'base' values at 0 for now
        rot = getRotationMatrix(frame["y"], frame["z"], frame["x"])
        val = np.dot(rot, np.array([value["x"], value["y"], value["z"]]))
        ik_params.append(list(val))

# DO NOT IMPORT UNLESS YOU KNOW WHAT YOU ARE DOING
ik = Actuator(ik_params)


# Import this to get IK support
def getIK(x, y, z):
    ik.ee = [x, y, z]

    controls = {}

    for index, key in enumerate(controlIndices):
        controls[key] = ik.angles[index]  # ik angles are in rad

    return controls


# Import this to move arm with IK
def moveTo(x, y, z):
    _controls = getIK(x, y, z)

    for key, value in _controls.items():
        controls[key].angle = np.rad2deg(value)


if __name__ == "__main__":
    while True:
        inp = input("(x y z | exit)> ").strip()

        if inp == "exit":
            break

        x, y, z = map(lambda n: float(str(n).strip()), inp.split(" "))

        vals = getIK(x, y, z)

        for key, value in vals.items():
            print(f"{key}: {np.rad2deg(value):.4f} deg")
