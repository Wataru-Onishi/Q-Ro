from dynamixel_sdk import *  # Dynamixel SDK library

# ---- セットアップ ----
DEVICENAME = '/dev/ttyUSB0'
BAUDRATE = 57600
PROTOCOL_VERSION = 2.0
DXL_ID = 1
ADDR_TORQUE_ENABLE = 64
ADDR_GOAL_POSITION = 116
ADDR_PRESENT_POSITION = 132
TORQUE_ENABLE = 1
TORQUE_DISABLE = 0

portHandler = PortHandler(DEVICENAME)
packetHandler = PacketHandler(PROTOCOL_VERSION)

# ---- ポートオープン ----
if not portHandler.openPort():
    print("ポートを開けませんでした")
    quit()
if not portHandler.setBaudRate(BAUDRATE):
    print("ボーレート設定失敗")
    quit()

# ---- トルクON ----
packetHandler.write1ByteTxRx(portHandler, DXL_ID, ADDR_TORQUE_ENABLE, TORQUE_ENABLE)

# ---- ゴール位置設定（0～4095）----
goal_position = 2048
packetHandler.write4ByteTxRx(portHandler, DXL_ID, ADDR_GOAL_POSITION, goal_position)

# ---- 現在位置取得 ----
dxl_present_position, _, _ = packetHandler.read4ByteTxRx(portHandler, DXL_ID, ADDR_PRESENT_POSITION)
print("現在位置:", dxl_present_position)

# ---- ポートを閉じる ----
portHandler.closePort()
