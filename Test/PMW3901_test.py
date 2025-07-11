from pmw3901 import PMW3901
import time

def main():
    try:
        sensor = PMW3901()
        print("PMW3901 初期化完了。動作を開始します。")
    except Exception as e:
        print("センサ初期化に失敗しました:", e)
        return

    total_dx = 0
    total_dy = 0
    start_time = time.time()

    try:
        while True:
            dx, dy = sensor.get_motion()
            total_dx += dx
            total_dy += dy
            print(f"dx: {dx}, dy: {dy}")

            time.sleep(0.01)

            if time.time() - start_time >= 1.0:
                print(f"1秒間の合計移動量 → dx: {total_dx}, dy: {total_dy}")
                total_dx = 0
                total_dy = 0
                start_time = time.time()

    except KeyboardInterrupt:
        print("\nテストを終了しました。")

if __name__ == '__main__':
    main()
