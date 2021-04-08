import adafruit_dotstar
import time
import board


class dotstar:
    def __init__(self):
        # Turn off the bright LED called a DotStar
        self.dotstar = adafruit_dotstar.DotStar(
            board.APA102_SCK, board.APA102_MOSI, 1, brightness=255.0, auto_write=True
        )
        self.dotstar[0] = (0, 0, 0, 0.0)

    def red(self):
        self.dotstar[0] = (255, 0, 0, 10.0)

    def green(self):
        self.dotstar[0] = (0, 255, 0, 10.0)

    def blue(self):
        self.dotstar[0] = (0, 0, 255, 10.0)

    def off(self):
        self.dotstar[0] = (0, 0, 0, 0.0)


myDot = dotstar()
while True:
    myDot.off()
    time.sleep(2)
    myDot.red()
    time.sleep(2)
    myDot.blue()
    time.sleep(2)
    myDot.green()
    time.sleep(2)
