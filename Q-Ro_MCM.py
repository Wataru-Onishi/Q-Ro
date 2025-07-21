import pygame
import time
from dynamixel_sdk import *  # Dynamixel SDK

# Dynamixel settings
DEVICENAME = '/dev/dynamixel'
BAUDRATE = 57600
PROTOCOL_VERSION = 2.0

DXL_IDS = [1, 2, 3, 4]  # ← ID4 を追加

ADDR_TORQUE_ENABLE = 64
ADDR_OPERATING_MODE = 11
ADDR_GOAL_VELOCITY = 104
ADDR_GOAL_POSITION = 116
POSITION_CONTROL_MODE = 3

TORQUE_ENABLE = 1
TORQUE_DISABLE = 0
VELOCITY_CONTROL_MODE = 1

# モーターごとの回転方向定数（1:正転, -1:逆転）
MOTOR_DIRECTION = {
    1: 1,
    2: -1,
    4: -1,  # ID4も正方向（逆転が必要ならここを -1 に変更）
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

# ✅ ID3（非走行）をブレーキ状態で初期化
packetHandler.write1ByteTxRx(portHandler, 3, ADDR_TORQUE_ENABLE, TORQUE_DISABLE)
packetHandler.write1ByteTxRx(portHandler, 3, ADDR_OPERATING_MODE, VELOCITY_CONTROL_MODE)
packetHandler.write1ByteTxRx(portHandler, 3, ADDR_TORQUE_ENABLE, TORQUE_ENABLE)
print("ID3: Torque enabled for brake mode.")

# ✅ ID1, ID2, ID4（走行系）の初期化
for dxl_id in [1, 2, 4]:
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
        pygame.event.pump()

        axis_y = joystick.get_axis(1)  # Y軸: 前後
        axis_x = joystick.get_axis(0)  # X軸: 旋回

        SCALE_Y = 200
        SCALE_X = 200

        forward_velocity = int(-axis_y * SCALE_Y)
        turning_velocity = int(axis_x * SCALE_X)

        velocity_id1 = (forward_velocity + turning_velocity) * MOTOR_DIRECTION[1]
        velocity_id2 = (forward_velocity - turning_velocity) * MOTOR_DIRECTION[2]

        # ID1, ID2 に速度指令
        packetHandler.write4ByteTxRx(portHandler, 1, ADDR_GOAL_VELOCITY, velocity_id1)
        packetHandler.write4ByteTxRx(portHandler, 2, ADDR_GOAL_VELOCITY, velocity_id2)

        # ID4 の制御：旋回時はブレーキ、前後進のみ同期
        if abs(axis_x) < 0.1:  # 旋回していない（前後進中）
            velocity_id4 = forward_velocity * MOTOR_DIRECTION[4]
        else:
            velocity_id4 = 0  # 旋回時はブレーキ

        packetHandler.write4ByteTxRx(portHandler, 4, ADDR_GOAL_VELOCITY, velocity_id4)

        print(f"Y: {axis_y:.2f}, X: {axis_x:.2f} | ID1: {velocity_id1}, ID2: {velocity_id2}, ID4: {velocity_id4}")

        # ボタン入力処理（A/BボタンでID3の位置制御）
        for event in pygame.event.get():
            if event.type == pygame.JOYBUTTONDOWN:
                if event.button == 0:  # Aボタン → 1400へ
                    packetHandler.write1ByteTxRx(portHandler, 3, ADDR_TORQUE_ENABLE, TORQUE_DISABLE)
                    packetHandler.write1ByteTxRx(portHandler, 3, ADDR_OPERATING_MODE, POSITION_CONTROL_MODE)
                    packetHandler.write1ByteTxRx(portHandler, 3, ADDR_TORQUE_ENABLE, TORQUE_ENABLE)
                    packetHandler.write4ByteTxRx(portHandler, 3, ADDR_GOAL_POSITION, 1400)
                    print("ID3: Move to position 1400")

                elif event.button == 1:  # Bボタン → 1600へ
                    packetHandler.write1ByteTxRx(portHandler, 3, ADDR_TORQUE_ENABLE, TORQUE_DISABLE)
                    packetHandler.write1ByteTxRx(portHandler, 3, ADDR_OPERATING_MODE, POSITION_CONTROL_MODE)
                    packetHandler.write1ByteTxRx(portHandler, 3, ADDR_TORQUE_ENABLE, TORQUE_ENABLE)
                    packetHandler.write4ByteTxRx(portHandler, 3, ADDR_GOAL_POSITION, 1600)
                    print("ID3: Move to position 1600")

        time.sleep(0.1)

except KeyboardInterrupt:
    print("Exiting...")

finally:
    for dxl_id in DXL_IDS:
        packetHandler.write4ByteTxRx(portHandler, dxl_id, ADDR_GOAL_VELOCITY, 0)
        packetHandler.write1ByteTxRx(portHandler, dxl_id, ADDR_TORQUE_ENABLE, TORQUE_DISABLE)

    portHandler.closePort()
    pygame.quit()
