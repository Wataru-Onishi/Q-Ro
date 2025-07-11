from pmw3901 import PMW3901
import time
import math

# =======================================
# センサ高さをここで指定（単位：mm）
SENSOR_HEIGHT_MM = 20
# =======================================

# 高さからピクセル→mm変換係数を推定
# 目安: 1ピクセル ≒ 0.0017 × 高さ(mm)
PIXEL_TO_MM = 0.0017 * SENSOR_HEIGHT_MM

def main():
    print(f"センサ高さ: {SENSOR_HEIGHT_MM}mm, 変換係数: {PIXEL_TO_MM:.4f} mm/pixel")
    try:
        sensor = PMW3901()
        print("PMW3901 初期化完了。動作を開始します。")
    except Exception as e:
        print("センサ初期化に失敗しました:", e)
        return

    total_dx_mm = 0.0
    total_dy_mm = 0.0
    start_time = time.time()

    try:
        while True:
            dx, dy = sensor.get_motion()
            dx_mm = dx * PIXEL_TO_MM
            dy_mm = dy * PIXEL_TO_MM

            total_dx_mm += dx_mm
            total_dy_mm += dy_mm

            distance = math.sqrt(dx_mm**2 + dy_mm**2)

            print(f"dx: {dx} ({dx_mm:.2f}mm), dy: {dy} ({dy_mm:.2f}mm), 移動距離: {distance:.2f}mm")

            time.sleep(0.01)

            if time.time() - start_time >= 1.0:
                total_distance = math.sqrt(total_dx_mm**2 + total_dy_mm**2)
                print(f"\n[1秒間の合計移動量] dx: {total_dx_mm:.2f}mm, dy: {total_dy_mm:.2f}mm, 距離: {total_distance:.2f}mm\n")
                total_dx_mm = 0.0
                total_dy_mm = 0.0
                start_time = time.time()

    except KeyboardInterrupt:
        print("\nテストを終了しました。")

if __name__ == '__main__':
    main()
