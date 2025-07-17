import pygame
import time
from dynamixel_sdk import *

# --- 1. Dynamixel 基本設定 ---
# ご自身の環境に合わせて変更してください
DEVICENAME = '/dev/dynamixel'  # Windowsの場合は 'COM3' など
BAUDRATE = 57600
PROTOCOL_VERSION = 2.0

# 制御する全モーターのID
DXL_IDS = [1, 2, 3, 4]

# Dynamixelコントロールテーブルのアドレス (Xシリーズ用)
ADDR_TORQUE_ENABLE = 64
ADDR_OPERATING_MODE = 11
ADDR_GOAL_VELOCITY = 104

# 操作モードの定数
TORQUE_ENABLE = 1
TORQUE_DISABLE = 0
VELOCITY_CONTROL_MODE = 1

# --- 2. ロボットの構成設定 ---
# ★★★ ロボットに合わせて要調整 ★★★
# 各モーターの回転方向を補正します。
# 前進させたときに逆回転するモーターがあれば、値を `1` から `-1` に変更してください。
# 一般的な対向配置では、左右どちらかのモーターを逆にする必要があります。
MOTOR_DIRECTION = {
    1: 1,   # 左前モーター
    2: 1,  # 右前モーター
    3: 1,   # 左後モーター
    4: 1,  # 右後モーター
}

# --- 3. DynamixelとPygameの初期化 ---
# Dynamixel ハンドラの初期化
portHandler = PortHandler(DEVICENAME)
packetHandler = PacketHandler(PROTOCOL_VERSION)

# ポートを開く
if not portHandler.openPort():
    print(f"ポート {DEVICENAME} を開けませんでした。")
    exit(1)
print(f"ポート {DEVICENAME} を開きました。")

# ボーレートを設定
if not portHandler.setBaudRate(BAUDRATE):
    print(f"ボーレート {BAUDRATE} を設定できませんでした。")
    exit(1)
print(f"ボーレートを {BAUDRATE} に設定しました。")

# 全てのモーターを「速度制御モード」に設定
for dxl_id in DXL_IDS:
    # モード変更の前に一度トルクを無効化
    packetHandler.write1ByteTxRx(portHandler, dxl_id, ADDR_TORQUE_ENABLE, TORQUE_DISABLE)
    # 速度制御モードに設定
    packetHandler.write1ByteTxRx(portHandler, dxl_id, ADDR_OPERATING_MODE, VELOCITY_CONTROL_MODE)
    # トルクを有効化
    packetHandler.write1ByteTxRx(portHandler, dxl_id, ADDR_TORQUE_ENABLE, TORQUE_ENABLE)
    print(f"ID {dxl_id}: 速度制御モードで初期化完了。")

# Pygame (ジョイスティック) の初期化
pygame.init()
pygame.joystick.init()
if pygame.joystick.get_count() == 0:
    print("ジョイスティックが見つかりません！")
    exit(1)
joystick = pygame.joystick.Joystick(0)
joystick.init()
print(f"ジョイスティック '{joystick.get_name()}' が接続されました。")

# --- 4. メインコントロールループ ---
try:
    print("\nロボットの操作を開始します。終了するには Ctrl+C を押してください。")
    # デッドゾーンの閾値 (0.0 から 1.0 の範囲で設定)
    # この値を大きくすると、スティックを大きく傾けないと反応しなくなります
    DEADZONE_THRESHOLD = 0.15 # 0.1から少し増やしました。必要に応じて調整してください。

    while True:
        # ジョイスティックのイベントを処理
        pygame.event.pump()

        # スティックの傾きを取得 (-1.0 から 1.0)
        # ジョイスティックは上方向が-1.0のことが多いので、-を付けて反転
        axis_y = -joystick.get_axis(1)  # 前後
        axis_x = joystick.get_axis(0)   # 旋回

        # --- デッドゾーンの適用 ---
        if abs(axis_y) < DEADZONE_THRESHOLD:
            axis_y = 0
        if abs(axis_x) < DEADZONE_THRESHOLD:
            axis_x = 0
        # ------------------------

        # 速度のスケール (この値が大きいほどモーターは速く回転します)
        VELOCITY_SCALE = 200

        # 前後と旋回の基本速度を計算
        forward_velocity = int(axis_y * VELOCITY_SCALE)
        turning_velocity = int(axis_x * VELOCITY_SCALE)

        # 左右の車輪の最終的な速度を計算 (スキッドステア)
        velocity_left = forward_velocity + turning_velocity
        velocity_right = forward_velocity - turning_velocity

        # 各モーターに速度を指令
        # 左側 (ID 1, 3)
        packetHandler.write4ByteTxRx(portHandler, 3, ADDR_GOAL_VELOCITY, velocity_left * MOTOR_DIRECTION[3])
        packetHandler.write4ByteTxRx(portHandler, 4, ADDR_GOAL_VELOCITY, velocity_left * MOTOR_DIRECTION[4])

        # 右側 (ID 2, 4)
        packetHandler.write4ByteTxRx(portHandler, 1, ADDR_GOAL_VELOCITY, velocity_right * MOTOR_DIRECTION[1])
        packetHandler.write4ByteTxRx(portHandler, 2, ADDR_GOAL_VELOCITY, velocity_right * MOTOR_DIRECTION[2])

        # 現在の指令値を表示 (デバッグ用)
        print(f"L:{velocity_left:4d}, R:{velocity_right:4d} | Fwd:{forward_velocity:4d}, Turn:{turning_velocity:4d}", end='\r')

        # ループの待機時間
        time.sleep(0.05)

except KeyboardInterrupt:
    print("\nプログラムを終了します...")

finally:
    # 安全のため、全てのモーターを停止してトルクをOFFにする
    print("全モーターを停止中...")
    for dxl_id in DXL_IDS:
        packetHandler.write4ByteTxRx(portHandler, dxl_id, ADDR_GOAL_VELOCITY, 0)
        time.sleep(0.05) # 指令が届くのを少し待つ
        packetHandler.write1ByteTxRx(portHandler, dxl_id, ADDR_TORQUE_ENABLE, TORQUE_DISABLE)

    # ポートを閉じてPygameを終了
    portHandler.closePort()
    pygame.quit()
    print("クリーンアップ完了。")