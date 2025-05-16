import pygame
import time
from dynamixel_sdk import *  # Dynamixel SDK

# Dynamixel settings
DEVICENAME = '/dev/ttyUSB0'
BAUDRATE = 57600
PROTOCOL_VERSION = 2.0

DXL_IDS = [1, 2]

ADDR_TORQUE_ENABLE = 64
ADDR_OPERATING_MODE = 11
ADDR_GOAL_VELOCITY = 104

TORQUE_ENABLE = 1
TORQUE_DISABLE = 0
VELOCITY_CONTROL_MODE = 1

# Initialize Dynamixel Port & Packet Handler
portHandler = PortHandler(DEVICENAME)
packetHandler = PacketHandler(PROTOCOL_VERSION)

# Open port
if not portHandler.openPort():
    print("Failed to open port!")
    exit(1)

# Set baudrate
if not portHandler.setBaudRate(BAUDRATE):
    print("Failed to set baudrate!")
    exit(1)

# Set Operating Mode to Velocity Control & Enable Torque
for dxl_id in DXL_IDS:
    packetHandler.write1ByteTxRx(portHandler, dxl_id, ADDR_TORQUE_ENABLE, 0)
    packetHandler.write1ByteTxRx(portHandler, dxl_id, ADDR_OPERATING_MODE, VELOCITY_CONTROL_MODE)
    packetHandler.write1ByteTxRx(portHandler, dxl_id, ADDR_TORQUE_ENABLE, TORQUE_ENABLE)

# Initialize pygame joystick
pygame.init()
pygame.joystick.init()

joystick = pygame.joystick.Joystick(0)
joystick.init()

print(f"Joystick Name: {joystick.get_name()} connected!")

try:
    while True:
        pygame.event.pump()  # Update joystick states

        axis_value = joystick.get_axis(1)  # Left stick Y-axis
        # Y軸は上で-1.0、下で+1.0 → 逆にするなら-をつける
        velocity = int(axis_value * 500)  # 適当なスケール値

        # Dynamixelに速度指令
        for dxl_id in DXL_IDS:
            packetHandler.write4ByteTxRx(portHandler, dxl_id, ADDR_GOAL_VELOCITY, abs(velocity))

        print(f"Joystick Y-axis: {axis_value:.2f}, Velocity Command: {velocity}")
        time.sleep(0.1)

except KeyboardInterrupt:
    print("Exiting...")

finally:
    # Stop motors and disable torque
    for dxl_id in DXL_IDS:
        packetHandler.write4ByteTxRx(portHandler, dxl_id, ADDR_GOAL_VELOCITY, 0)
        packetHandler.write1ByteTxRx(portHandler, dxl_id, ADDR_TORQUE_ENABLE, TORQUE_DISABLE)

    portHandler.closePort()
    pygame.quit()
