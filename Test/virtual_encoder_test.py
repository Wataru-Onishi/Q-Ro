import RPi.GPIO as GPIO
import time
import math
from pmw3901 import PMW3901

# ==============================================================================
# --- 設定項目 ---
# ==============================================================================

# 1. GPIOピン設定 (BCM番号で指定)
PIN_A = 17  # A相信号に使用するGPIOピン
PIN_B = 27  # B相信号に使用するGPIOピン
PIN_Z = 22  # Z相信号に使用するGPIOピン

# 2. 仮想エンコーダのパラメータ
# <<< 最も重要な調整項目です >>>
# 何ミリの直線移動を仮想的な1回転とみなすかを定義します。
MM_PER_REV = 150.0

# エンコーダの分解能（仕様書およびご指定の値）
PULSES_PER_REV = 300 # [cite: 39]

# 3. PMW3901センサーのパラメータ
SENSOR_HEIGHT_MM = 30
PIXEL_TO_MM = 0.0017 * SENSOR_HEIGHT_MM

# ==============================================================================
# --- スクリプト本体 (ここから下は変更不要です) ---
# ==============================================================================

# --- グローバル変数 ---
encoder_pos = 0  # 起動時からの総パルス数を保持
last_quad_state = -1  # GPIOへの不要な書き込みを避けるため、最後の状態を保存

# データシートの波形図に基づく直交状態テーブル (A, B)
# CW (時計回り):  State 0 -> 1 -> 2 -> 3 -> 0
# CCW (反時計回り): State 0 -> 3 -> 2 -> 1 -> 0
quadrature_table = [
    (0, 0),  # State 0
    (1, 0),  # State 1
    (1, 1),  # State 2
    (0, 1)   # State 3
]

def setup_gpio():
    """GPIOピンを初期化します。"""
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(PIN_A, GPIO.OUT)
    GPIO.setup(PIN_B, GPIO.OUT)
    GPIO.setup(PIN_Z, GPIO.OUT)
    # 初期状態を (A=0, B=0, Z=0) に設定
    GPIO.output(PIN_A, 0)
    GPIO.output(PIN_B, 0)
    GPIO.output(PIN_Z, 0)
    print("GPIOピンを初期化しました。")

def update_encoder_outputs(state):
    """直交状態に基づいてGPIO出力を更新し、Z相パルスを処理します。"""
    global last_quad_state
    if state == last_quad_state:
        return  # 状態に変化がなければ何もしない

    a_val, b_val = quadrature_table[state]
    GPIO.output(PIN_A, a_val)
    GPIO.output(PIN_B, b_val)

    # Z相パルス（インデックスパルス）を生成
    # 1回転の開始時（encoder_posがPULSES_PER_REVの倍数）にHighになり、
    # 1つの直交ステップの間だけHighを維持します。
    pulses_in_rev = encoder_pos % PULSES_PER_REV
    if pulses_in_rev == 0 and state == 0:
        GPIO.output(PIN_Z, 1)
    else:
        GPIO.output(PIN_Z, 0)

    last_quad_state = state

def main():
    """仮想エンコーダを動作させるメイン関数。"""
    global encoder_pos
    
    print("仮想エンコーダプログラムを開始します...")
    print("---")
    print(f"エンコーダ分解能: {PULSES_PER_REV} P/R")
    print(f"1回転あたりの移動距離: {MM_PER_REV} mm")
    mm_per_pulse = MM_PER_REV / PULSES_PER_REV
    print(f"1パルスあたりの必要移動距離: {mm_per_pulse:.4f} mm")
    print("---")
    print(f"センサーの高さ: {SENSOR_HEIGHT_MM}mm")
    print(f"距離変換係数: {PIXEL_TO_MM:.4f} mm/pixel")
    print("---")

    setup_gpio()
    update_encoder_outputs(0) # 初期状態を設定

    try:
        sensor = PMW3901()
        print("PMW3901センサーの初期化に成功しました。移動量の読み取りを開始します...")
    except Exception as e:
        print(f"センサーの初期化に失敗しました: {e}")
        GPIO.cleanup()
        return

    accumulated_distance_mm = 0.0

    try:
        while True:
            # 1. センサーから移動量を取得
            try:
                dx, dy = sensor.get_motion()
            except Exception as e:
                print(f"センサーからの読み取りエラー: {e}")
                time.sleep(0.5)
                continue

            # 2. ピクセル単位の移動量をmmに変換
            # この実装では「dy」を前後方向の移動に使用します。
            # 必要に応じて「dx」や総移動距離 `math.sqrt(dx**2 + dy**2)` に変更してください。
            motion_mm = dy * PIXEL_TO_MM
            accumulated_distance_mm += motion_mm

            # 3. 累積移動距離に基づいてパルスを生成
            # 前進 (時計回り)
            while accumulated_distance_mm >= mm_per_pulse:
                encoder_pos += 1
                new_state = encoder_pos % 4
                update_encoder_outputs(new_state)
                accumulated_distance_mm -= mm_per_pulse

            # 後退 (反時計回り)
            while accumulated_distance_mm <= -mm_per_pulse:
                encoder_pos -= 1
                new_state = encoder_pos % 4
                update_encoder_outputs(new_state)
                accumulated_distance_mm += mm_per_pulse
            
            # CPU使用率が100%になるのを防ぐために短い待機時間を入れます。
            # このループの性能が、最大パルス周波数を決定します。
            time.sleep(0.001)

    except KeyboardInterrupt:
        print("\nプログラムがユーザーによって停止されました。")
    finally:
        print("GPIOをクリーンアップしています...")
        GPIO.cleanup()
        print("完了。")

if __name__ == '__main__':
    main()