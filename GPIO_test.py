import RPi.GPIO as GPIO
import time

# GPIO番号指定の準備
GPIO.setmode(GPIO.BCM)

# Raspberry Piによく使われるGPIOピンのリスト
# 使用するラズベリーパイのモデルに応じて、このリストを調整してください
pins = [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27]

# GPIOピンの設定
for pin in pins:
    GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

try:
    while True:
        # 全ピンの状態を読み取り、表示
        print("現在のGPIOピンの状態:")
        for pin in pins:
            state = GPIO.input(pin)
            print(f"GPIO{pin}: {'HIGH' if state else 'LOW'}")
        
        # 更新速度（ここでは1秒毎に更新）
        print("-----")
        time.sleep(1)

except KeyboardInterrupt:
    print("プログラム終了")

finally:
    GPIO.cleanup()
