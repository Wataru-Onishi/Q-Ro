import os
import pygame
from pygame.locals import *
from dynamixel_sdk import *  # Uses Dynamixel SDK library

# Pygame and controller initialization
pygame.init()
pygame.joystick.init()
joystick = pygame.joystick.Joystick(0)
joystick.init()

# Define button mappings
BUTTON_MOVE_TO_POSITION_X = 0  # X button on PS4 controller
BUTTON_MOVE_TO_STANDARD_POSITION = 1  # Circle button on PS4 controller
BUTTON_TOGGLE_CURRENT_LIMIT = 2  # Triangle button on PS4 controller
BUTTON_BRAKE_MOTORS = 4  # L1 button on PS4 controller
BUTTON_EXIT_PROGRAM = 10  # PS button on PS4 controller

# Define hat (D-pad) mappings
HAT_UP = (1, 0)        # D-pad Up
HAT_DOWN = (0, -1)     # D-pad Down
HAT_RIGHT = (0, 1)     # D-pad Right
HAT_LEFT = (-1, 0)     # D-pad Left

# Dynamixel control table addresses
ADDR_OPERATING_MODE = 11
ADDR_TORQUE_ENABLE = 64
ADDR_GOAL_CURRENT = 102
ADDR_GOAL_VELOCITY = 104  # For velocity control
ADDR_GOAL_POSITION = 116
ADDR_PRESENT_POSITION = 132

# Dynamixel data byte lengths
LEN_GOAL_CURRENT = 2
LEN_GOAL_POSITION = 4

# Protocol version
PROTOCOL_VERSION = 2.0

# Dynamixel settings
DXL_IDS = [1, 2, 3]  # Dynamixel motor IDs
BAUDRATE = 57600
DEVICENAME = '/dev/DYNAMIXEL'  # Device port name
TORQUE_ENABLE = 1
TORQUE_DISABLE = 0

# Operating modes
CURRENT_BASED_POSITION_CONTROL = 5
POSITION_CONTROL_MODE = 3
VELOCITY_CONTROL_MODE = 1

# Current limit settings
CURRENT_LIMIT_HIGH = 12
CURRENT_LIMIT_LOW = 4
current_limit = CURRENT_LIMIT_HIGH  # Initial current limit in mA

# Position and velocity settings
new_goal_position = 900  # New goal position for the X button
standard_position = 1800
forward_velocity = 100
backward_velocity = -100
turning_velocity = 100

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
    enable_torque([id], TORQUE_DISABLE)  # Disable torque before changing mode
    packetHandler.write1ByteTxRx(portHandler, id, ADDR_OPERATING_MODE, mode)
    enable_torque([id], TORQUE_ENABLE)  # Re-enable torque after changing mode

def set_goal_current(id, current):
    packetHandler.write2ByteTxRx(portHandler, id, ADDR_GOAL_CURRENT, current)

def set_goal_position(id, position):
    packetHandler.write4ByteTxRx(portHandler, id, ADDR_GOAL_POSITION, position)

def set_goal_velocity(id, velocity):
    packetHandler.write4ByteTxRx(portHandler, id, ADDR_GOAL_VELOCITY, velocity)

# Enable torque for all motors
enable_torque(DXL_IDS, TORQUE_ENABLE)

print("Dynamixel has been successfully connected and controller is ready.")

try:
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == JOYBUTTONDOWN:
                if event.button == BUTTON_MOVE_TO_POSITION_X:
                    set_operating_mode(1, CURRENT_BASED_POSITION_CONTROL)
                    set_goal_current(1, current_limit)
                    set_goal_position(1, new_goal_position)
                    print(f"ID 1: Moving to position {new_goal_position} with {current_limit}mA.")
                elif event.button == BUTTON_MOVE_TO_STANDARD_POSITION:
                    set_operating_mode(1, POSITION_CONTROL_MODE)
                    set_goal_position(1, standard_position)
                    print(f"ID 1: Moving to position {standard_position}.")
                elif event.button == BUTTON_TOGGLE_CURRENT_LIMIT:
                    current_limit = CURRENT_LIMIT_LOW if current_limit == CURRENT_LIMIT_HIGH else CURRENT_LIMIT_HIGH
                    print(f"Current limit toggled to {current_limit}mA.")
                elif event.button == BUTTON_BRAKE_MOTORS:
                    set_goal_velocity(2, 0)
                    set_goal_velocity(3, 0)
                    print("Braking Motors 2 and 3.")
                elif event.button == BUTTON_EXIT_PROGRAM:
                    print("PS button pressed. Exiting program.")
                    running = False
            elif event.type == JOYHATMOTION:
                if joystick.get_hat(0) == HAT_UP:
                    set_operating_mode(2, VELOCITY_CONTROL_MODE)
                    set_operating_mode(3, VELOCITY_CONTROL_MODE)
                    set_goal_velocity(2, forward_velocity)
                    set_goal_velocity(3, forward_velocity)
                    print("Motors 2 and 3 are set to move forward at controlled speed.")
                elif joystick.get_hat(0) == HAT_DOWN:
                    set_operating_mode(2, VELOCITY_CONTROL_MODE)
                    set_operating_mode(3, VELOCITY_CONTROL_MODE)
                    set_goal_velocity(2, backward_velocity)
                    set_goal_velocity(3, backward_velocity)
                    print("Motors 2 and 3 are set to move backward at controlled speed.")
                elif joystick.get_hat(0) == HAT_RIGHT:
                    set_operating_mode(2, VELOCITY_CONTROL_MODE)
                    set_operating_mode(3, VELOCITY_CONTROL_MODE)
                    set_goal_velocity(2, turning_velocity)
                    set_goal_velocity(3, -turning_velocity)
                    print("Turning right with Motors 2 and 3.")
                elif joystick.get_hat(0) == HAT_LEFT:
                    set_operating_mode(2, VELOCITY_CONTROL_MODE)
                    set_operating_mode(3, VELOCITY_CONTROL_MODE)
                    set_goal_velocity(2, -turning_velocity)
                    set_goal_velocity(3, turning_velocity)
                    print("Turning left with Motors 2 and 3.")
finally:
    enable_torque(DXL_IDS, TORQUE_DISABLE)  # Disable torque on exit
    portHandler.closePort()
    pygame.quit()
