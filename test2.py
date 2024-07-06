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
LEN_GOAL_VELOCITY = 4
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
CURRENT_CONTROL_MODE = 0
POSITION_CONTROL_MODE = 3
VELOCITY_CONTROL_MODE = 1  # For velocity control

# Goal settings for ID 1
goal_current_for_wall_mA = 3  # in mA
goal_position_1 = 1800  # Example position

# Velocity settings for IDs 2 & 3
goal_velocity_forward = 100  # Positive for forward
goal_velocity_backward = -100  # Negative for backward
turning_velocity = 100  # Velocity for turning

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

def set_goal_velocity(id, velocity):
    packetHandler.write4ByteTxRx(portHandler, id, ADDR_GOAL_VELOCITY, velocity)

def set_goal_position(id, position):
    packetHandler.write4ByteTxRx(portHandler, id, ADDR_GOAL_POSITION, position)

def get_present_position(id):
    present_position, _, _ = packetHandler.read4ByteTxRx(portHandler, id, ADDR_PRESENT_POSITION)
    return present_position

# Enable torque for all motors
enable_torque([DXL_ID_1, DXL_ID_2, DXL_ID_3], TORQUE_ENABLE)

print("Dynamixel has been successfully connected and controller is ready.")

try:
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == JOYBUTTONDOWN:
                if joystick.get_button(0):  # X button
                    set_operating_mode(DXL_ID_1, CURRENT_CONTROL_MODE)
                    set_goal_current(DXL_ID_1, goal_current_for_wall_mA)
                    set_goal_position(DXL_ID_1, goal_position_1)
                    print(f"ID 1: Moving to position {goal_position_1} with {goal_current_for_wall_mA}mA current.")
                elif joystick.get_button(1):  # Circle button
                    set_operating_mode(DXL_ID_1, POSITION_CONTROL_MODE)
                    set_goal_position(DXL_ID_1, goal_position_1)
                    print(f"ID 1: Moving to position {goal_position_1}.")
                elif joystick.get_button(4):  # L1 button
                    set_goal_velocity(DXL_ID_2, 0)  # Stop motor 2
                    set_goal_velocity(DXL_ID_3, 0)  # Stop motor 3
                    print("Braking Motors 2 and 3.")
            elif event.type == JOYHATMOTION:
                if joystick.get_hat(0) == (0, 1):  # D-pad Up
                    set_operating_mode(DXL_ID_2, VELOCITY_CONTROL_MODE)
                    set_operating_mode(DXL_ID_3, VELOCITY_CONTROL_MODE)
                    set_goal_velocity(DXL_ID_2, -goal_velocity_forward)
                    set_goal_velocity(DXL_ID_3, goal_velocity_forward)
                    print("Motors 2 and 3 are set to move forward at controlled speed.")
                elif joystick.get_hat(0) == (0, -1):  # D-pad Down
                    set_operating_mode(DXL_ID_2, VELOCITY_CONTROL_MODE)
                    set_operating_mode(DXL_ID_3, VELOCITY_CONTROL_MODE)
                    set_goal_velocity(DXL_ID_2, -goal_velocity_backward)
                    set_goal_velocity(DXL_ID_3, goal_velocity_backward)
                    print("Motors 2 and 3 are set to move backward at controlled speed.")
                elif joystick.get_hat(0) == (1, 0):  # D-pad Right
                    set_operating_mode(DXL_ID_2, VELOCITY_CONTROL_MODE)
                    set_operating_mode(DXL_ID_3, VELOCITY_CONTROL_MODE)
                    set_goal_velocity(DXL_ID_2, turning_velocity)  # Motor 2 turns backward
                    set_goal_velocity(DXL_ID_3, turning_velocity)  # Motor 3 turns forward
                    print("Turning right with Motors 2 and 3.")
                elif joystick.get_hat(0) == (-1, 0):  # D-pad Left
                    set_operating_mode(DXL_ID_2, VELOCITY_CONTROL_MODE)
                    set_operating_mode(DXL_ID_3, VELOCITY_CONTROL_MODE)
                    set_goal_velocity(DXL_ID_2, -turning_velocity)  # Motor 2 turns forward
                    set_goal_velocity(DXL_ID_3, -turning_velocity)  # Motor 3 turns backward
                    print("Turning left with Motors 2 and 3.")
            elif event.type == pygame.QUIT:
                running = False

        # Check if ID 1 has reached the goal position
        if set_operating_mode == CURRENT_CONTROL_MODE:
            current_position = get_present_position(DXL_ID_1)
            if abs(current_position - goal_position_1) < 10:  # Tolerance of 10 units
                set_goal_current(DXL_ID_1, 0)  # Stop the motor
                print(f"ID 1: Reached position {goal_position_1} and stopped.")

finally:
    enable_torque([DXL_ID_1, DXL_ID_2, DXL_ID_3], TORQUE_DISABLE)  # Disable torque on exit
    portHandler.closePort()
    pygame.quit()
