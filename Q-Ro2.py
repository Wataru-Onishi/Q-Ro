import os
import time
import pygame
from pygame.locals import *
from dynamixel_sdk import *  # Uses Dynamixel SDK library

# Pygame and controller initialization
pygame.init()
pygame.joystick.init()
joystick = pygame.joystick.Joystick(0)
joystick.init()

# Define button mappings
BUTTON_MOVE_TO_POSITION_X = 0
BUTTON_MOVE_TO_STANDARD_POSITION = 1
BUTTON_TOGGLE_CURRENT_LIMIT = 2
BUTTON_BRAKE_MOTORS = 4
BUTTON_TOGGLE_MODE = 5
BUTTON_EXIT_PROGRAM = 10

# Define hat (D-pad) mappings
HAT_UP = (0, 1)
HAT_DOWN = (0, -1)
HAT_RIGHT = (1, 0)
HAT_LEFT = (-1, 0)

# Timing constants for auto mode operations
STOP_DURATION = 1  # Time to stop in seconds
RIGHT_TURN_DURATION = 2.7  # Time to turn right in seconds
LEFT_TURN_DURATION = 2.7  # Time to turn left in seconds
MOVE_FORWARD_DURATION = 2  # Time to move forward in seconds

# Dynamixel control table addresses
ADDR_OPERATING_MODE = 11
ADDR_TORQUE_ENABLE = 64
ADDR_GOAL_CURRENT = 102
ADDR_GOAL_VELOCITY = 104
ADDR_GOAL_POSITION = 116
ADDR_PRESENT_POSITION = 132

# Protocol version
PROTOCOL_VERSION = 2.0

# Dynamixel settings
TORQUE_CONTROL_ID = 0  # Torque control is assigned to ID 0
DXL_IDS = [1, 2, 3, 4]  # Motor IDs 1-4 are used for driving
BAUDRATE = 57600
DEVICENAME = '/dev/DYNAMIXEL'
TORQUE_ENABLE = 1
TORQUE_DISABLE = 0

# Operating modes
CURRENT_BASED_POSITION_CONTROL = 5
POSITION_CONTROL_MODE = 3
VELOCITY_CONTROL_MODE = 1

# Current limit settings
CURRENT_LIMIT_HIGH = 12
CURRENT_LIMIT_LOW = 2
current_limit = CURRENT_LIMIT_HIGH

# Position and velocity settings
standard_position = 400
new_goal_position = 2300
velocity_value = 250  # Base velocity value
TURNING_SPEED = 150  # Speed for turning movements

# Mode settings
MANUAL_MODE = 0
AUTO_MODE = 1
current_mode = MANUAL_MODE

# Define motor direction constants for forward, backward, left, and right turns
FORWARD_DIRECTION = {
    1: velocity_value,
    2: -velocity_value,
    3: velocity_value,
    4: -velocity_value
}

BACKWARD_DIRECTION = {
    1: -velocity_value,
    2: velocity_value,
    3: -velocity_value,
    4: velocity_value
}

RIGHT_TURN_DIRECTION = {
    1: TURNING_SPEED,   # Speed for right turn
    2: TURNING_SPEED,   # Speed for ID 2
    3: TURNING_SPEED,   # Speed for ID 3
    4: TURNING_SPEED    # Speed for right turn
}

LEFT_TURN_DIRECTION = {
    1: -TURNING_SPEED,  # Speed for left turn
    2: -TURNING_SPEED,  # Speed for ID 2
    3: -TURNING_SPEED,  # Speed for ID 3
    4: -TURNING_SPEED   # Speed for left turn
}

# Initialize PortHandler and PacketHandler instances
portHandler = PortHandler(DEVICENAME)
packetHandler = PacketHandler(PROTOCOL_VERSION)

# Open port and set baudrate
if not portHandler.openPort():
    print("Failed to open the port!")
    quit()
if not portHandler.setBaudRate(BAUDRATE):
    print("Failed to change the baudrate!")
    quit()

def enable_torque(ids, enable):
    for id in ids:
        packetHandler.write1ByteTxRx(portHandler, id, ADDR_TORQUE_ENABLE, enable)

def set_operating_mode(id, mode):
    enable_torque([id], TORQUE_DISABLE)
    packetHandler.write1ByteTxRx(portHandler, id, ADDR_OPERATING_MODE, mode)
    enable_torque([id], TORQUE_ENABLE)

def set_goal_velocity(id, velocity):
    packetHandler.write4ByteTxRx(portHandler, id, ADDR_GOAL_VELOCITY, velocity)

def move_motors(direction):
    for motor_id, velocity in direction.items():
        set_goal_velocity(motor_id, velocity)

def set_goal_current(id, current):
    packetHandler.write2ByteTxRx(portHandler, id, ADDR_GOAL_CURRENT, current)

def set_goal_position(id, position):
    packetHandler.write4ByteTxRx(portHandler, id, ADDR_GOAL_POSITION, position)

# Enable torque for all driving motors (IDs 1-4)
enable_torque(DXL_IDS, TORQUE_ENABLE)

# Enable torque for the torque control motor (ID 0)
enable_torque([TORQUE_CONTROL_ID], TORQUE_ENABLE)

print("Dynamixel has been successfully connected and controller is ready.")

try:
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == JOYBUTTONDOWN:
                if event.button == BUTTON_TOGGLE_MODE:
                    current_mode = AUTO_MODE if current_mode == MANUAL_MODE else MANUAL_MODE
                    if current_mode == AUTO_MODE:
                        move_motors({1: 0, 2: 0, 3: 0, 4: 0})  # Stop all motors when entering auto mode
                        print("Switched to AUTO MODE. Motors stopped.")
                    else:
                        print("Switched to MANUAL MODE.")
                elif event.button == BUTTON_BRAKE_MOTORS:
                    move_motors({1: 0, 2: 0, 3: 0, 4: 0})
                    print("Braking Motors 1, 2, 3, and 4.")
                elif event.button == BUTTON_EXIT_PROGRAM:
                    print("PS button pressed. Exiting program.")
                    running = False

                # Restore ID 0 torque control functionality
                if event.button == BUTTON_MOVE_TO_POSITION_X:
                    set_operating_mode(TORQUE_CONTROL_ID, CURRENT_BASED_POSITION_CONTROL)
                    set_goal_current(TORQUE_CONTROL_ID, current_limit)
                    set_goal_position(TORQUE_CONTROL_ID, new_goal_position)
                    print(f"ID 0 (Torque control): Moving to position {new_goal_position} with {current_limit}mA.")
                elif event.button == BUTTON_MOVE_TO_STANDARD_POSITION:
                    set_operating_mode(TORQUE_CONTROL_ID, POSITION_CONTROL_MODE)
                    set_goal_position(TORQUE_CONTROL_ID, standard_position)
                    print(f"ID 0 (Torque control): Moving to standard position {standard_position}.")
                elif event.button == BUTTON_TOGGLE_CURRENT_LIMIT:
                    current_limit = CURRENT_LIMIT_LOW if current_limit == CURRENT_LIMIT_HIGH else CURRENT_LIMIT_HIGH
                    print(f"Current limit toggled to {current_limit}mA.")

            elif event.type == JOYHATMOTION:
                if current_mode == MANUAL_MODE:
                    if joystick.get_hat(0) == HAT_UP:
                        move_motors(FORWARD_DIRECTION)
                        print("Motors are set to move forward at controlled speed.")
                    elif joystick.get_hat(0) == HAT_DOWN:
                        move_motors(BACKWARD_DIRECTION)
                        print("Motors are set to move backward at controlled speed.")
                    elif joystick.get_hat(0) == HAT_RIGHT:
                        move_motors(RIGHT_TURN_DIRECTION)
                        print("Turning right with adjusted velocities.")
                    elif joystick.get_hat(0) == HAT_LEFT:
                        move_motors(LEFT_TURN_DIRECTION)
                        print("Turning left with adjusted velocities.")
finally:
    enable_torque(DXL_IDS, TORQUE_DISABLE)
    enable_torque([TORQUE_CONTROL_ID], TORQUE_DISABLE)
    portHandler.closePort()
    pygame.quit()
