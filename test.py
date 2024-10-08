import os
import pygame
from pygame.locals import *
from dynamixel_sdk import *  # Uses Dynamixel SDK library

# Pygame and controller initialization
pygame.init()
pygame.joystick.init()
joystick = pygame.joystick.Joystick(0)
joystick.init()

# Control table address
ADDR_OPERATING_MODE = 11
ADDR_TORQUE_ENABLE = 64
ADDR_GOAL_CURRENT = 102
ADDR_GOAL_VELOCITY = 104  # For velocity control
ADDR_GOAL_POSITION = 116
ADDR_PRESENT_POSITION = 132

# Data Byte Length
LEN_GOAL_CURRENT = 2
LEN_GOAL_POSITION = 4

# Protocol version
PROTOCOL_VERSION = 2.0

# Default setting
DXL_ID_1 = 1  # Dynamixel ID for the original motor
DXL_ID_2 = 2  # Dynamixel ID for the first new motor
DXL_ID_3 = 3  # Dynamixel ID for the second new motor
BAUDRATE = 57600
DEVICENAME = '/dev/DYNAMIXEL'  # The port being used

TORQUE_ENABLE = 1
TORQUE_DISABLE = 0

# Operating Modes
CURRENT_BASED_POSITION_CONTROL = 5
POSITION_CONTROL_MODE = 3
VELOCITY_CONTROL_MODE = 1

# Current limit constants
CURRENT_LIMIT_HIGH = 12
CURRENT_LIMIT_LOW = 4
current_limit = CURRENT_LIMIT_HIGH  # Default current in mA

# New Goal settings for ID 1 when X button is pressed
new_goal_position = 900  # Position to move to

# Standard positions and velocities
standard_position = 1800
forward_velocity = 100
backward_velocity = -100
turning_velocity = 100

# Initialize PortHandler instance
portHandler = PortHandler(DEVICENAME)

# Initialize PacketHandler instance
packetHandler = PacketHandler(PROTOCOL_VERSION)

# Open port
if not portHandler.openPort():
    print("Failed to open the port!")
    quit()

# Set port baudrate
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
enable_torque([DXL_ID_1, DXL_ID_2, DXL_ID_3], TORQUE_ENABLE)

print("Dynamixel has been successfully connected and controller is ready.")

try:
    running = True
    num_buttons = joystick.get_numbuttons()  # Get the number of buttons on the joystick
    while running:
        for event in pygame.event.get():
            if event.type == JOYBUTTONDOWN:
                if event.button < num_buttons:  # Validate button index before using it
                    button = event.button
                    # Process button events
                    if button == 0:
                        set_operating_mode(DXL_ID_1, CURRENT_BASED_POSITION_CONTROL)
                        set_goal_current(DXL_ID_1, current_limit)
                        set_goal_position(DXL_ID_1, new_goal_position)
                        print(f"ID 1: Moving to position {new_goal_position} with {current_limit}mA.")
                    elif button == 1:
                        set_operating_mode(DXL_ID_1, POSITION_CONTROL_MODE)
                        set_goal_position(DXL_ID_1, standard_position)
                        print(f"ID 1: Moving to position {standard_position}.")
                    elif button == 2:
                        current_limit = CURRENT_LIMIT_LOW if current_limit == CURRENT_LIMIT_HIGH else CURRENT_LIMIT_HIGH
                        print(f"Current limit toggled to {current_limit}mA.")
                    elif button == 4:
                        set_goal_velocity(DXL_ID_2, 0)
                        set_goal_velocity(DXL_ID_3, 0)
                        print("Braking Motors 2 and 3.")
                    elif button == 10:  # PS button
                        print("PS button pressed. Exiting program.")
                        running = False
                    else:
                        print(f"Button {button} pressed but no action defined.")
                else:
                    print(f"Button {event.button} is out of range and has no defined action.")
            elif event.type == JOYHATMOTION:
                if joystick.get_hat(0) == (0, 1):  # D-pad Up
                    set_operating_mode(DXL_ID_2, VELOCITY_CONTROL_MODE)
                    set_operating_mode(DXL_ID_3, VELOCITY_CONTROL_MODE)
                    set_goal_velocity(DXL_ID_2, forward_velocity)
                    set_goal_velocity(DXL_ID_3, forward_velocity)
                    print("Motors 2 and 3 are set to move forward at controlled speed.")
                elif joystick.get_hat(0) == (0, -1):  # D-pad Down
                    set_operating_mode(DXL_ID_2, VELOCITY_CONTROL_MODE)
                    set_operating_mode(DXL_ID_3, VELOCITY_CONTROL_MODE)
                    set_goal_velocity(DXL_ID_2, backward_velocity)
                    set_goal_velocity(DXL_ID_3, backward_velocity)
                    print("Motors 2 and 3 are set to move backward at controlled speed.")
                elif joystick.get_hat(0) == (1, 0):  # D-pad Right
                    set_operating_mode(DXL_ID_2, VELOCITY_CONTROL_MODE)
                    set_operating_mode(DXL_ID_3, VELOCITY_CONTROL_MODE)
                    set_goal_velocity(DXL_ID_2, turning_velocity)
                    set_goal_velocity(DXL_ID_3, -turning_velocity)
                    print("Turning right with Motors 2 and 3.")
                elif joystick.get_hat(0) == (-1, 0):  # D-pad Left
                    set_operating_mode(DXL_ID_2, VELOCITY_CONTROL_MODE)
                    set_operating_mode(DXL_ID_3, VELOCITY_CONTROL_MODE)
                    set_goal_velocity(DXL_ID_2, -turning_velocity)
                    set_goal_velocity(DXL_ID_3, turning_velocity)
                    print("Turning left with Motors 2 and 3.")
            elif event.type == pygame.QUIT:
                running = False
finally:
    enable_torque([DXL_ID_1, DXL_ID_2, DXL_ID_3], TORQUE_DISABLE)  # Disable torque on exit
    portHandler.closePort()
    pygame.quit()
