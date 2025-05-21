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
ADDR_GOAL_POSITION = 116  # ← 追加
POSITION_CONTROL_MODE = 3  # ← 追加

TORQUE_ENABLE = 1
TORQUE_DISABLE = 0
VELOCITY_CONTROL_MODE = 1

# モーターごとの回転方向定数（1:正転, -1:逆転）
MOTOR_DIRECTION = {
    1: 1,    # ID1 正転
    2: -1,   # ID2 逆転（対向二輪ならここを-1）
}

# Dynamixel 初期化
portHandler = PortHandler(DEVICENAME)
packetHandler = PacketHandler(PROTOCOL_VERSION)

if not portHandler.openPort():
    print("Failed to open port!")
    exit(1)

if not portHandler.setBaudRate(BAUDRATE):
    print("Failed to set baudrate!")
    exit(1)

# ✅ ID3はブレーキ固定用（最初にトルクON）
packetHandler.write1ByteTxRx(portHandler, 3, ADDR_TORQUE_ENABLE, TORQUE_DISABLE)
packetHandler.write1ByteTxRx(portHandler, 3, ADDR_OPERATING_MODE, VELOCITY_CONTROL_MODE)
packetHandler.write1ByteTxRx(portHandler, 3, ADDR_TORQUE_ENABLE, TORQUE_ENABLE)
print("ID3: Torque enabled for brake mode.")

# モード設定とトルクON（ID1, ID2）
for dxl_id in [1, 2]:
    packetHandler.write1ByteTxRx(portHandler, dxl_id, ADDR_TORQUE_ENABLE, TORQUE_DISABLE)
    packetHandler.write1ByteTxRx(portHandler, dxl_id, ADDR_OPERATING_MODE, VELOCITY_CONTROL_MODE)
    packetHandler.write1ByteTxRx(portHandler, dxl_id, ADDR_TORQUE_ENABLE, TORQUE_ENABLE)

# Pygameでジョイスティック初期化
pygame.init()
pygame.joystick.init()

joystick = pygame.joystick.Joystick(0)
joystick.init()

print(f"Joystick Name: {joystick.get_name()} connected!")

try:
    while True:
        pygame.event.pump()  # ジョイスティック状態更新

        # 左スティックY軸（前後）とX軸（旋回）
        axis_y = joystick.get_axis(1)
        axis_x = joystick.get_axis(0)

        # スケール値（速度倍率）
        SCALE_Y = 200
        SCALE_X = 200

        # 速度計算
        forward_velocity = int(-axis_y * SCALE_Y)
        turning_velocity = int(axis_x * SCALE_X)

        velocity_id1 = (forward_velocity + turning_velocity) * MOTOR_DIRECTION[1]
        velocity_id2 = (forward_velocity - turning_velocity) * MOTOR_DIRECTION[2]

        # モーターに速度指令
        packetHandler.write4ByteTxRx(portHandler, 1, ADDR_GOAL_VELOCITY, velocity_id1)
        packetHandler.write4ByteTxRx(portHandler, 2, ADDR_GOAL_VELOCITY, velocity_id2)

        print(f"Y: {axis_y:.2f}, X: {axis_x:.2f} | ID1 Velocity: {velocity_id1} | ID2 Velocity: {velocity_id2}")

        # ボタン入力処理（A/BボタンでID3の位置制御）
        for event in pygame.event.get():
            if event.type == pygame.JOYBUTTONDOWN:
                if event.button == 0:  # Aボタン
                    packetHandler.write1ByteTxRx(portHandler, 3, ADDR_TORQUE_ENABLE, TORQUE_DISABLE)
                    packetHandler.write1ByteTxRx(portHandler, 3, ADDR_OPERATING_MODE, POSITION_CONTROL_MODE)
                    packetHandler.write1ByteTxRx(portHandler, 3, ADDR_TORQUE_ENABLE, TORQUE_ENABLE)
                    packetHandler.write4ByteTxRx(portHandler, 3, ADDR_GOAL_POSITION, 1400)
                    print("ID3: Move to position 1000")

                elif event.button == 1:  # Bボタン
                    packetHandler.write1ByteTxRx(portHandler, 3, ADDR_TORQUE_ENABLE, TORQUE_DISABLE)
                    packetHandler.write1ByteTxRx(portHandler, 3, ADDR_OPERATING_MODE, POSITION_CONTROL_MODE)
                    packetHandler.write1ByteTxRx(portHandler, 3, ADDR_TORQUE_ENABLE, TORQUE_ENABLE)
                    packetHandler.write4ByteTxRx(portHandler, 3, ADDR_GOAL_POSITION, 1600)
                    print("ID3: Move to position 1500")

        time.sleep(0.1)

except KeyboardInterrupt:
    print("Exiting...")

finally:
    for dxl_id in DXL_IDS:
        packetHandler.write4ByteTxRx(portHandler, dxl_id, ADDR_GOAL_VELOCITY, 0)
        packetHandler.write1ByteTxRx(portHandler, dxl_id, ADDR_TORQUE_ENABLE, TORQUE_DISABLE)

    portHandler.closePort()
    pygame.quit()
