import pygame
import time
from dynamixel_sdk import *  # Dynamixel SDK

# Dynamixel settings
DEVICENAME = '/dev/dynamixel'
BAUDRATE = 57600
PROTOCOL_VERSION = 2.0

DXL_IDS = [1, 2, 3]

ADDR_TORQUE_ENABLE = 64
ADDR_OPERATING_MODE = 11
ADDR_GOAL_VELOCITY = 104
ADDR_GOAL_POSITION = 116
ADDR_GOAL_CURRENT = 102

TORQUE_ENABLE = 1
TORQUE_DISABLE = 0
VELOCITY_CONTROL_MODE = 1
POSITION_CONTROL_MODE = 3
CURRENT_BASED_POSITION_CONTROL = 5

# モーターごとの回転方向定数（1:正転, -1:逆転）
MOTOR_DIRECTION = {
    1: 1,    # ID1 正転
    2: -1,   # ID2 逆転（対向二輪）
}

# ID3 制御用パラメータ
CURRENT_LIMIT_HIGH = 12
CURRENT_LIMIT_LOW = 2
current_limit = CURRENT_LIMIT_HIGH
standard_position = 1800
new_goal_position = -100

# SDK初期化
portHandler = PortHandler(DEVICENAME)
packetHandler = PacketHandler(PROTOCOL_VERSION)

if not portHandler.openPort():
    print("Failed to open port!")
    exit(1)

if not portHandler.setBaudRate(BAUDRATE):
    print("Failed to set baudrate!")
    exit(1)

# ID3（以前のID1の動作）用の初期化（最初はトルクON・速度0）
packetHandler.write1ByteTxRx(portHandler, 3, ADDR_TORQUE_ENABLE, 0)
packetHandler.write1ByteTxRx(portHandler, 3, ADDR_OPERATING_MODE, VELOCITY_CONTROL_MODE)
packetHandler.write1ByteTxRx(portHandler, 3, ADDR_TORQUE_ENABLE, TORQUE_ENABLE)
print("ID3: Torque enabled (initial brake mode)")

# ID1, ID2 → 速度制御・トルクON
for dxl_id in [1, 2]:
    packetHandler.write1ByteTxRx(portHandler, dxl_id, ADDR_TORQUE_ENABLE, 0)
    packetHandler.write1ByteTxRx(portHandler, dxl_id, ADDR_OPERATING_MODE, VELOCITY_CONTROL_MODE)
    packetHandler.write1ByteTxRx(portHandler, dxl_id, ADDR_TORQUE_ENABLE, TORQUE_ENABLE)

# Pygame初期化
pygame.init()
pygame.joystick.init()
joystick = pygame.joystick.Joystick(0)
joystick.init()
print(f"Joystick Name: {joystick.get_name()} connected!")

try:
    while True:
        pygame.event.pump()

        # 左スティックのY軸・X軸
        axis_y = joystick.get_axis(1)
        axis_x = joystick.get_axis(0)

        SCALE_Y = 200
        SCALE_X = 200

        forward_velocity = int(-axis_y * SCALE_Y)
        turning_velocity = int(axis_x * SCALE_X)

        velocity_id1 = (forward_velocity + turning_velocity) * MOTOR_DIRECTION[1]
        velocity_id2 = (forward_velocity - turning_velocity) * MOTOR_DIRECTION[2]

        # ID1, ID2 に速度指令
        packetHandler.write4ByteTxRx(portHandler, 1, ADDR_GOAL_VELOCITY, velocity_id1)
        packetHandler.write4ByteTxRx(portHandler, 2, ADDR_GOAL_VELOCITY, velocity_id2)

        print(f"Y: {axis_y:.2f}, X: {axis_x:.2f} | ID1: {velocity_id1}, ID2: {velocity_id2}")

        # ボタンイベント処理
        for event in pygame.event.get():
            if event.type == pygame.JOYBUTTONDOWN:
                if event.button == 0:  # Aボタン → 電流制御で押し込む
                    packetHandler.write1ByteTxRx(portHandler, 3, ADDR_TORQUE_ENABLE, 0)
                    packetHandler.write1ByteTxRx(portHandler, 3, ADDR_OPERATING_MODE, CURRENT_BASED_POSITION_CONTROL)
                    packetHandler.write1ByteTxRx(portHandler, 3, ADDR_TORQUE_ENABLE, TORQUE_ENABLE)
                    packetHandler.write2ByteTxRx(portHandler, 3, ADDR_GOAL_CURRENT, current_limit)
                    packetHandler.write4ByteTxRx(portHandler, 3, ADDR_GOAL_POSITION, new_goal_position)
                    print(f"ID3: Move to position {new_goal_position} with {current_limit}mA (current-based)")

                elif event.button == 1:  # Bボタン → 標準位置へ戻る（位置制御）
                    packetHandler.write1ByteTxRx(portHandler, 3, ADDR_TORQUE_ENABLE, 0)
                    packetHandler.write1ByteTxRx(portHandler, 3, ADDR_OPERATING_MODE, POSITION_CONTROL_MODE)
                    packetHandler.write1ByteTxRx(portHandler, 3, ADDR_TORQUE_ENABLE, TORQUE_ENABLE)
                    packetHandler.write4ByteTxRx(portHandler, 3, ADDR_GOAL_POSITION, standard_position)
                    print(f"ID3: Move to standard position {standard_position}")

                elif event.button == 2:  # Xボタン → 電流制限切り替え
                    current_limit = CURRENT_LIMIT_LOW if current_limit == CURRENT_LIMIT_HIGH else CURRENT_LIMIT_HIGH
                    print(f"Current limit toggled to {current_limit}mA")

        time.sleep(0.1)

except KeyboardInterrupt:
    print("Exiting...")

finally:
    for dxl_id in DXL_IDS:
        packetHandler.write4ByteTxRx(portHandler, dxl_id, ADDR_GOAL_VELOCITY, 0)
        packetHandler.write1ByteTxRx(portHandler, dxl_id, ADDR_TORQUE_ENABLE, TORQUE_DISABLE)

    portHandler.closePort()
    pygame.quit()
