import RPi.GPIO as GPIO
import time
import math
from pmw3901 import PMW3901 # 実際のセンサーを使う場合はコメントアウトを解除
import sys

# RPi.GPIOライブラリのインポートを試み、失敗した場合はダミーのモックライブラリを使用する
try:
    import RPi.GPIO as GPIO
    print("RPi.GPIO library loaded successfully.")
except (ModuleNotFoundError, RuntimeError):
    print("WARNING: RPi.GPIO not found. Using a mock library for testing on PC.")
    # --- ダミーのGPIOクラス ---
    class MockGPIO:
        BCM = "BCM"
        OUT = "OUT"
        def setmode(self, mode): print(f"Mock GPIO: Set mode to {mode}")
        def setup(self, pin, mode): print(f"Mock GPIO: Setup pin {pin} as {mode}")
        def output(self, pin, value): pass
        def cleanup(self): print("Mock GPIO: Cleanup called.")
    GPIO = MockGPIO()
    # --- ダミーのPMW3901クラス (PCテスト用) ---
    class PMW3901:
        def __init__(self): print("Mock PMW3901 Initialized")
        def get_motion(self):
            # テスト用にランダムな動きをシミュレート
            import random
            return random.randint(-5, 5), random.randint(-10, 10)

# ==============================================================================
# --- CONFIGURATION ---
# ==============================================================================
PIN_A = 17
PIN_B = 27
PIN_Z = 22
MM_PER_REV = 150.0
PULSES_PER_REV = 300
SENSOR_HEIGHT_MM = 30
PIXEL_TO_MM = 0.0017 * SENSOR_HEIGHT_MM

# ==============================================================================
# --- SCRIPT ---
# ==============================================================================
encoder_pos = 0
last_quad_state = -1
quadrature_table = [(0, 0), (1, 0), (1, 1), (0, 1)]

def setup_gpio():
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(PIN_A, GPIO.OUT)
    GPIO.setup(PIN_B, GPIO.OUT)
    GPIO.setup(PIN_Z, GPIO.OUT)
    GPIO.output(PIN_A, 0)
    GPIO.output(PIN_B, 0)
    GPIO.output(PIN_Z, 0)
    print("GPIOピンを初期化しました。")

def update_encoder_outputs(state):
    global last_quad_state
    if state == last_quad_state: return
    a_val, b_val = quadrature_table[state]
    GPIO.output(PIN_A, a_val)
    GPIO.output(PIN_B, b_val)
    pulses_in_rev = encoder_pos % PULSES_PER_REV
    GPIO.output(PIN_Z, 1 if pulses_in_rev == 0 and state == 0 else 0)
    last_quad_state = state

def main():
    global encoder_pos
    print("仮想エンコーダプログラムを開始します...")
    setup_gpio()
    update_encoder_outputs(0)

    try:
        sensor = PMW3901()
        print("PMW3901センサーの初期化に成功しました。移動量の読み取りを開始します...")
    except Exception as e:
        print(f"センサーの初期化に失敗しました: {e}")
        GPIO.cleanup()
        return

    accumulated_distance_mm = 0.0
    mm_per_pulse = MM_PER_REV / PULSES_PER_REV

    # --- 可視化のための変数 ---
    last_print_time = time.time()
    print_interval = 0.2  # 0.2秒ごとに表示
    accumulated_dx = 0
    accumulated_dy = 0
    # --------------------------

    try:
        while True:
            # 1. センサーから移動量を取得
            try:
                dx, dy = sensor.get_motion()
                # --- 可視化のための値を加算 ---
                accumulated_dx += dx
                accumulated_dy += dy
                # ------------------------------
            except Exception as e:
                print(f"センサーからの読み取りエラー: {e}")
                time.sleep(0.5)
                continue

            # 2. mmに変換し、パルスを生成
            motion_mm = dy * PIXEL_TO_MM
            accumulated_distance_mm += motion_mm
            while accumulated_distance_mm >= mm_per_pulse:
                encoder_pos += 1
                update_encoder_outputs(encoder_pos % 4)
                accumulated_distance_mm -= mm_per_pulse
            while accumulated_distance_mm <= -mm_per_pulse:
                encoder_pos -= 1
                update_encoder_outputs(encoder_pos % 4)
                accumulated_distance_mm += mm_per_pulse
            
            # --- 3. 定期的に移動量をコンソールに表示 ---
            current_time = time.time()
            if current_time - last_print_time >= print_interval:
                # 単位をピクセルからmmに変換
                total_motion_mm_y = accumulated_dy * PIXEL_TO_MM

                # 表示
                print(f"Interval Read: dx={accumulated_dx:4d} px, dy={accumulated_dy:4d} px | Motion Y: {total_motion_mm_y:7.3f} mm | Encoder Pulse: {encoder_pos}")

                # 加算値をリセット
                accumulated_dx = 0
                accumulated_dy = 0
                last_print_time = current_time
            # ----------------------------------------
            
            time.sleep(0.001)

    except KeyboardInterrupt:
        print("\nプログラムがユーザーによって停止されました。")
    finally:
        print("GPIOをクリーンアップしています...")
        GPIO.cleanup()
        print("完了。")

if __name__ == '__main__':
    main()