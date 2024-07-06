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
ADDR_PROPORTIONAL_GAIN = 80  # Adjust these addresses based on your model
ADDR_INTEGRAL_GAIN = 82
ADDR_DERIVATIVE_GAIN = 84

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
CURRENT_LIMIT_HIGH = 20
CURRENT_LIMIT_LOW = 10
current_limit = CURRENT_LIMIT_HIGH  # Default current in mA

# New Goal settings for ID 1 when X button is pressed
new_goal_position = 900  # Position to move to

# Standard positions and velocities
standard_position = 1800
forward_velocity = 200
backward_velocity = -200
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
    num_buttons = joystick.get_numbuttons()  # ジョイスティックのボタン数を取得
    while running:
        for event in pygame.event.get():
            if event.type == JOYBUTTONDOWN:
                button_id = event.button  # 押されたボタンのIDを取得
                if button_id < num_buttons:  # ボタンIDが有効な範囲内かチェック
                    if joystick.get_button(0):  # X button
                        set_operating_mode(DXL_ID_1, CURRENT_BASED_POSITION_CONTROL)
                        set_goal_current(DXL_ID_1, current_limit)
                        set_goal_position(DXL_ID_1, new_goal_position)
                        print(f"ID 1: Moving to position {new_goal_position} with {current_limit}mA.")
                    elif joystick.get_button(1):  # Circle button
                        set_operating_mode(DXL_ID_1, POSITION_CONTROL_MODE)
                        set_goal_position(DXL_ID_1, standard_position)
                        print(f"ID 1: Moving to position {standard_position}.")
                    elif joystick.get_button(2):  # Square button
                        current_limit = CURRENT_LIMIT_LOW if current_limit == CURRENT_LIMIT_HIGH else CURRENT_LIMIT_HIGH
                        print(f"Current limit toggled to {current_limit}mA.")
                    elif joystick.get_button(4):  # L1 button
                        set_goal_velocity(DXL_ID_2, 0)  # Stop motor 2
                        set_goal_velocity(DXL_ID_3, 0)  # Stop motor 3
                        print("Braking Motors 2 and 3.")
                    elif joystick.get_button(13):  # PS button
                        print("PS button pressed. Exiting program.")
                        running = False
                    else:
                        print(f"Button {button_id} pressed but no action defined.")
                else:
                    print(f"Button {button_id} is out of range and has no defined action.")
            elif event.type == JOYHATMOTION:
                # 同様のハットスイッチ処理...
            elif event.type == pygame.QUIT:
                running = False
finally:
    enable_torque([DXL_ID_1, DXL_ID_2, DXL_ID_3], TORQUE_DISABLE)  # Disable torque on exit
    portHandler.closePort()
    pygame.quit()

