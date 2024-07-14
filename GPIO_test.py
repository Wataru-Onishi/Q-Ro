import RPi.GPIO as GPIO
import time

# GPIO番号指定の準備
GPIO.setmode(GPIO.BCM)

# GPIOピンの設定
pins = [16, 20, 21, 19]
for pin in pins:
    GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

try:
    while True:
        # 各ピンの状態を読み取り、表示
        for pin in pins:
            state = GPIO.input(pin)
            print(f"GPIO{pin}: {'HIGH' if state else 'LOW'}")
        
        # 更新速度（ここでは1秒毎に更新）
        time.sleep(1)

except KeyboardInterrupt:
    print("プログラム終了")

finally:
    GPIO.cleanup()
