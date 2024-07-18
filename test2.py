import os
import pygame
import RPi.GPIO as GPIO
from pygame.locals import *
from dynamixel_sdk import *  # Uses Dynamixel SDK library

# Pygame and controller initialization
pygame.init()
pygame.joystick.init()
joystick = pygame.joystick.Joystick(0)
joystick.init()

# GPIO setup
sensor_pins = [16, 19, 20, 26]
GPIO.setmode(GPIO.BCM)
for pin in sensor_pins:
    GPIO.setup(pin, GPIO.IN)

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
DXL_IDS = [1, 2, 3]
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
CURRENT_LIMIT_LOW = 4
current_limit = CURRENT_LIMIT_HIGH

# Position and velocity settings
standard_position = 2048
forward_velocity = 100
backward_velocity = -100
turning_velocity = 50
new_goal_position = 4096

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
    packetHandler.write4ByteTxRx(portHandler, id, ADDR_GOAL_VELOCITY, velocity)

def check_stop_signal():
    return GPIO.input(26)  # Return the current state of GPIO 26

# Enable torque for all motors
enable_torque(DXL_IDS, TORQUE_ENABLE)

print("Dynamixel has been successfully connected and controller is ready.")

try:
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == JOYBUTTONDOWN:
                if event.button == BUTTON_TOGGLE_MODE:
                    current_mode = AUTO_MODE if current_mode == MANUAL_MODE else MANUAL_MODE
                    print(f"Mode changed to {'AUTO' if current_mode == AUTO_MODE else 'MANUAL'}.")
                elif event.button == BUTTON_BRAKE_MOTORS:
                    set_goal_velocity(2, 0)
                    set_goal_velocity(3, 0)
                    print("Braking Motors 2 and 3.")
                elif event.button == BUTTON_EXIT_PROGRAM:
                    print("PS button pressed. Exiting program.")
                    running = False

            elif event.type == JOYHATMOTION:
                if joystick.get_hat(0) == HAT_UP:
                    if current_mode == AUTO_MODE:
                        set_operating_mode(2, VELOCITY_CONTROL_MODE)
                        set_operating_mode(3, VELOCITY_CONTROL_MODE)
                        set_goal_velocity(2, forward_velocity)
                        set_goal_velocity(3, forward_velocity)
                        print("Initiated auto-forward in auto mode.")
                    elif current_mode == MANUAL_MODE:
                        set_operating_mode(2, VELOCITY_CONTROL_MODE)
                        set_operating_mode(3, VELOCITY_CONTROL_MODE)
                        set_goal_velocity(2, forward_velocity)
                        set_goal_velocity(3, forward_velocity)
                        print("Motors 2 and 3 are set to move forward at controlled speed.")

            # Check for stop signal in auto mode
            if current_mode == AUTO_MODE and check_stop_signal():
                set_goal_velocity(2, 0)
                set_goal_velocity(3, 0)
                print("Auto mode stop signal received. Motors stopped.")

finally:
    enable_torque(DXL_IDS, TORQUE_DISABLE)
    portHandler.closePort()
    pygame.quit()
    GPIO.cleanup()
