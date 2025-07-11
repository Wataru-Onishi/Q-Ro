from pmw3901 import PMW3901
import time

def main():
    # センサ初期化（CSピンを変更している場合は spi_cs=〇〇 を指定）
    sensor = PMW3901()
    

    print("PMW3901 初期化完了。動作を開始します。")
    
    total_dx = 0
    total_dy = 0
    start_time = time.time()

    try:
        while True:
            motion = sensor.get_motion()
            dx = motion['x']
            dy = motion['y']
            total_dx += dx
            total_dy += dy
            print(f"dx: {dx}, dy: {dy}")

            time.sleep(0.01)  # 約100Hzで読み取り（センサの仕様に近い）

            # 1秒ごとに合計移動量を表示
            if time.time() - start_time >= 1.0:
                print(f"1秒間の合計移動量 → dx: {total_dx}, dy: {total_dy}")
                total_dx = 0
                total_dy = 0
                start_time = time.time()

    except KeyboardInterrupt:
        print("\nテストを終了しました。")

if __name__ == '__main__':
    main()
