## Requirements

This thing requires the libraries in `requirements.txt`, as follows:
| Name | Version |
| --- | ---: |
| [gpiozero](https://pypi.org/project/gpiozero/) | ~1.6.2 |
| [tinyik](https://pypi.org/project/tinyik/) | ~2.2.1 |
| [numpy](https://pypi.org/project/numpy/) | ~1.24.3 |
| [PyYAML](https://pypi.org/project/PyYAML) | ~6.0.1 |

## Setup

- Start with `pip install gpiozero tinyik`
- Install one of
  | Name | Class | Install |
  | :---: | :--- | --- |
  | RPi.GPIO | `gpiozero.pins.rpigpio.RPiGPIOFactory` | Comes with Raspberry Pi |
  | pigpio | `gpiozero.pins.pigpio.PiGPIOFactory` | Install pigpio daemon, then see [pigpio.py](http://abyz.me.uk/rpi/pigpio/python.html)

  or anything listed at [gpiozero](https://gpiozero.readthedocs.io/en/stable/api_pins.html#changing-the-pin-factory) and set the output library: See [[Link]](https://gpiozero.readthedocs.io/en/stable/api_pins.html#changing-the-pin-factory)

## Usage

- import `controls` to get individual control. `controls` is a dictionary implementing `AngularServo` and `Motor` interfaces from `gpiozero.py`

  - To set the angle of a servo, set `servo.angle` in degrees
  - Motors implement `motor.backward()` and `motor.forward()`

- import `getIK()` or `moveTo()` to use IK. `getIK` returns a dictionary of the angles that controls should be at, in **radians**. `moveTo` performs the movement automatically.

  - If you set the IK to move to a position it cannot reach, it can produce invalid outputs
  - the IK library outputs values larger than 0

- You can set the output library of gpiozero:

- You can test the IK mechanism by running `python controls.py`

  - Enter `exit` to quit
  - Enter the target position in `<x> <y> <z>` format, the output will the intended positions of each servo in degrees

- Basic controls can be accessed with `python run.py`
  - Configuration for this is laid out in the `inputs` section in `confg.yaml`

## Types

- `controls: dict<AngularServo | Motor>`
- `getIK(x: float, y: float, z: float) => dict<float>`
- `moveTo(x: float, y: float, z: float) => None`

## Configuration

This script uses `confg.yaml` for configuration.

```yaml
controls:               # This is where all the controls are defined
  name:                 # The name of a control
    type: servo         # Required - type of control. servos map to `AngularServo`
    pin: 0              # Required - The GPIO pin for servos. MUST be PWN-enabled
    range: 180          # Required - The range of motion. Servos initialize at 0 deg
    pulse:
      min: 0.5          # Required - Min pulse length for servo control, in ms
      max: 2.5          # Required - Max pulse length for servo control, in ms
  name:
    type: actuator      # Required - actuators map to `Motor`
    pins:
      hi: 0             # Required - Active High pin for h-bridge
      lo: 0             # Required - Active Low pin for h-bridge

ik:                     # IK configuration block. List of IK blocks
  - control: name       # Required - name of control, corresponds to
                        #   name in `controls`
    axis: x | "y" | z   # Required - axis of control
    angle: 0            # Optional - starting angle of motor. Use for easier
                        #   configuration when motors are mounted not directly in
                        #   line with the arm. In Degrees

  - x: 0                # Required - X length of arm
    y: 0                # Required - Y length of arm
    z: 0                # Required - Z length of arm. Vertical Axis

inputs:                 # Where the inputs for run.py are (manual controls)
  button: 0             # Required - Pin for the button controlling the actuator
  vel: 0.1              # Required - the velocity at which positions are interpolated
                        #   in length for IK and SELECT, but degrees for POSITIONAL

  type: positional | ik # Required - positional has each axis naively controlled by moving
                        #   the servos, ik uses the IK system to get the servos' positions
  x: 0                  # Required MCP3008 channel
  y: 0                  # Required
  z: 0                  # Required

  type: select          # select is for control with only two axis joystick
  select: 0             # Required - MCP3008 channel that is used for selecting the axis
  main: 0               # Required - channel that is used for moving the axis
```
