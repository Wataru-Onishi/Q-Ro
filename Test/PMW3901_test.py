from pmw3901 import PMW3901
import time
import math

# =======================================
SENSOR_HEIGHT_MM = 30  # センサの床からの高さ (mm)
PIXEL_TO_MM = 0.0017 * SENSOR_HEIGHT_MM
# =======================================

def main():
    while True:
        print("------------------------------------------")
        print(f"センサ高さ: {SENSOR_HEIGHT_MM}mm, 変換係数: {PIXEL_TO_MM:.4f} mm/pixel")

        try:
            # センサーの初期化
            sensor = PMW3901()
            print("PMW3901 初期化完了。動作を開始します。")

            total_dx_mm = 0.0
            total_dy_mm = 0.0
            last_summary_time = time.time()

            # センサーからのデータ取得ループ
            while True:
                try:
                    # センサーから移動量を取得
                    dx, dy = sensor.get_motion()
                    dx_mm = dx * PIXEL_TO_MM
                    dy_mm = dy * PIXEL_TO_MM

                    total_dx_mm += dx_mm
                    total_dy_mm += dy_mm

                    now = time.time()

                    # 1秒ごとに合計移動距離を表示
                    if now - last_summary_time >= 1.0:
                        total_distance = math.sqrt(total_dx_mm**2 + total_dy_mm**2)
                        print(f"1秒間の移動距離 → dx: {total_dx_mm:.2f}mm, dy: {total_dy_mm:.2f}mm, 合成距離: {total_distance:.2f}mm")
                        total_dx_mm = 0.0
                        total_dy_mm = 0.0
                        last_summary_time = now

                    time.sleep(0.01)

                except Exception as e:
                    # センサー通信中にエラーが発生した場合
                    print(f"モーション取得中にエラーが発生しました: {e}")
                    print("SPIバスをリセットするため、再初期化を試みます。")
                    break  # 内側のループを抜けて、センサーの再初期化へ

        except Exception as e:
            # センサーの初期化に失敗した場合
            print(f"センサ初期化に失敗しました: {e}")
            print("1秒後に再試行します。")
            time.sleep(1)

        except KeyboardInterrupt:
            # プログラムを終了
            print("\nテストを終了しました。")
            break

if __name__ == '__main__':
    main()