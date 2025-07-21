import pygame
import time

pygame.init()
pygame.joystick.init()

if pygame.joystick.get_count() == 0:
    print("ゲームパッドが接続されていません。")
    exit()

joystick = pygame.joystick.Joystick(0)
joystick.init()
print(f"ゲームパッド名: {joystick.get_name()}")
print(f"ボタン数: {joystick.get_numbuttons()}")
print(f"軸数: {joystick.get_numaxes()}")
print(f"ハット数: {joystick.get_numhats()}")

try:
    while True:
        pygame.event.pump()

        buttons = [joystick.get_button(i) for i in range(joystick.get_numbuttons())]
        axes = [round(joystick.get_axis(i), 2) for i in range(joystick.get_numaxes())]
        hats = [joystick.get_hat(i) for i in range(joystick.get_numhats())]

        print("ボタン:", buttons)
        print("軸:", axes)
        print("ハット:", hats)
        print("-" * 40)
        time.sleep(0.2)

except KeyboardInterrupt:
    print("終了します。")
    pygame.quit()
