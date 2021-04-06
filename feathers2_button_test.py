import time
import board
import digitalio
import feathers2
import adafruit_dotstar


#
# Turn off the bright LED called a DotStar
#
dotstar = adafruit_dotstar.DotStar(board.APA102_SCK, board.APA102_MOSI, 1, brightness=0.0, auto_write=True)
dotstar[0] = ( 0, 0, 0, 0.0)
#
# Assign the pin address to button_a
#
button_a = digitalio.DigitalInOut(board.D13)
#
# Setup button_a as an input
#
button_a.direction = digitalio.Direction.INPUT
#
# Via software ground (pull down) the pin
#
button_a.pull = digitalio.Pull.DOWN
cnt = 0
#
# Run until we turn off the power or type ctrl-c
# in the serial console
#
print("Press the button ...")
while True:
    if button_a.value:
        cnt += 1
        print("Button Pressed: {}".format(cnt))
        #
        # turn on the blue LED
        #
        feathers2.led_set(True)
        #
        # Wait 2 seconds and turn it off
        #
        time.sleep(2)
        feathers2.led_set(False)
        print("Time to press the button again ...")

# End of the program
