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
LEFT_TURN_DURATION = 2.7  # Time to turn right in seconds
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
forward_velocity = 150
backward_velocity = -150
turning_velocity = 100
new_goal_position = 2300

# Mode settings
MANUAL_MODE = 0
AUTO_MODE = 1
current_mode = MANUAL_MODE

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

def set_goal_current(id, current):
    packetHandler.write2ByteTxRx(portHandler, id, ADDR_GOAL_CURRENT, current)

def set_goal_position(id, position):
    packetHandler.write4ByteTxRx(portHandler, id, ADDR_GOAL_POSITION, position)

def set_goal_velocity(id, velocity):
    if id == 2:
        velocity = -velocity  # Reverse velocity for ID 2
    elif id == 4:
        velocity = -velocity  # Reverse velocity for ID 4
    packetHandler.write4ByteTxRx(portHandler, id, ADDR_GOAL_VELOCITY, velocity)

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
                        set_goal_velocity(1, 0)  # Stop all motors when entering auto mode
                        set_goal_velocity(2, 0)
                        set_goal_velocity(3, 0)
                        set_goal_velocity(4, 0)
                        print("Switched to AUTO MODE. Motors stopped.")
                    else:
                        print("Switched to MANUAL MODE.")
                elif event.button == BUTTON_BRAKE_MOTORS:
                    set_goal_velocity(1, 0)
                    set_goal_velocity(2, 0)
                    set_goal_velocity(3, 0)
                    set_goal_velocity(4, 0)
                    print("Braking Motors 1, 2, 3, and 4.")
                elif event.button == BUTTON_EXIT_PROGRAM:
                    print("PS button pressed. Exiting program.")
                    running = False
                if current_mode == MANUAL_MODE:
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
                        set_operating_mode(1, VELOCITY_CONTROL_MODE)
                        set_operating_mode(2, VELOCITY_CONTROL_MODE)
                        set_operating_mode(3, VELOCITY_CONTROL_MODE)
                        set_operating_mode(4, VELOCITY_CONTROL_MODE)
                        set_goal_velocity(1, forward_velocity)
                        set_goal_velocity(2, forward_velocity)  # Reversed for ID 2
                        set_goal_velocity(3, forward_velocity)
                        set_goal_velocity(4, forward_velocity)
                        print("Motors 1, 2 (reversed), 3, and 4 are set to move forward at controlled speed.")
                    elif joystick.get_hat(0) == HAT_DOWN:
                        set_operating_mode(1, VELOCITY_CONTROL_MODE)
                        set_operating_mode(2, VELOCITY_CONTROL_MODE)
                        set_operating_mode(3, VELOCITY_CONTROL_MODE)
                        set_operating_mode(4, VELOCITY_CONTROL_MODE)
                        set_goal_velocity(1, backward_velocity)
                        set_goal_velocity(2, backward_velocity)  # Reversed for ID 2
                        set_goal_velocity(3, backward_velocity)
                        set_goal_velocity(4, backward_velocity)
                        print("Motors 1, 2 (reversed), 3, and 4 are set to move backward at controlled speed.")
                    elif joystick.get_hat(0) == HAT_RIGHT:
                        set_operating_mode(1, VELOCITY_CONTROL_MODE)
                        set_operating_mode(2, VELOCITY_CONTROL_MODE)
                        set_operating_mode(3, VELOCITY_CONTROL_MODE)
                        set_operating_mode(4, VELOCITY_CONTROL_MODE)
                        set_goal_velocity(1, turning_velocity)
                        set_goal_velocity(2, turning_velocity)  # Reversed for ID 2
                        set_goal_velocity(3, -turning_velocity)
                        set_goal_velocity(4, -turning_velocity)
                        print("Turning right with Motors 1, 2 (reversed), 3, and 4.")
                    elif joystick.get_hat(0) == HAT_LEFT:
                        set_operating_mode(1, VELOCITY_CONTROL_MODE)
                        set_operating_mode(2, VELOCITY_CONTROL_MODE)
                        set_operating_mode(3, VELOCITY_CONTROL_MODE)
                        set_operating_mode(4, VELOCITY_CONTROL_MODE)
                        set_goal_velocity(1, -turning_velocity)
                        set_goal_velocity(2, -turning_velocity)  # Reversed for ID 2
                        set_goal_velocity(3, turning_velocity)
                        set_goal_velocity(4, turning_velocity)
                        print("Turning left with Motors 1, 2 (reversed), 3, and 4.")
finally:
    enable_torque(DXL_IDS, TORQUE_DISABLE)
    enable_torque([TORQUE_CONTROL_ID], TORQUE_DISABLE)
    portHandler.closePort()
    pygame.quit()
