# Author: Irv Shapiro
# Website: https://cogitations.com
# YouTube Channel: https://youtube.com/c/drvax

# This program is derived from the Twilio example for microPython posted
# at https://www.twilio.com/blog/sms-doorbell-micropython-twilio

# It is also derived from various Adafruit CircuitPython web examples.

# Copyright 2020, Cogitations, LLC

# Permission is hereby granted, free of charge, to any
# person obtaining a copy of this software and associated
# documentation files  (the "Software"), to deal in the
# Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the
# Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice
# shall be included in all copies or substantial portions of
# the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY
# KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE
# WARRANTIES  OF MERCHANTABILITY, FITNESS FOR A PARTICULAR
# PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS
# ORCOPYRIGHT HOLDERS  BE LIABLE FOR ANY CLAIM, DAMAGES OR
# OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
# OTHERWISE, ARISING FROM, OUT  OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#

# When a button on pin 11 (data 13) is press an API call is
# placed to Twilio and a text messages is sent.  The message
# provided in secrets.py has the current time, based on the
# device IP address appended to the user provided text

# This file, secrets.py, is where you keep secret settings, passwords,
# and tokens! Do not put confidential informatiuon in the code
# that you share online.  PLEASE NOTE.  This informatuion is still
# on your device which you must secure.

# secrets.py must be stored on the device alongside code.py

# secrets = {
#     'ssid' : 'DrVax XXXXXXX',
#     'password' : 'Password---------',
#     'TWILIO_ACCOUNT_SID' : 'AC---------------------------',
#     'TWILIO_AUTH_TOKEN' : '-------------------------------',
#     'TWILIO_FROM_NUMBER' : '+13339998888',
#     'NOTIFICATION_NUMBER' : '+14445557777',
#     'message',
#     }
#
# Note the telephone numbers must begin with a country code

import ssl
import wifi
import socketpool
import adafruit_requests
import time
import board
import digitalio
import binascii
import adafruit_dotstar

# Get passwords and credentials
print("Loading network passwords")
try:
    from secrets import secrets
except ImportError:
    print("WiFi secrets are kept in secrets.py, please add them there!")
    raise

#
# This class connects the device to your local wifi based on a SID and
# password provided in the secrets.py file.  It first lists the SIDs it
# finds to the console to aid in debugging.
#
class connect_me:
    def connect_wifi():

        print("FeatherS2 Wifi Request with Button Test")

        print("My MAC addr:", [hex(i) for i in wifi.radio.mac_address])

        print("Available WiFi networks:")
        for network in wifi.radio.start_scanning_networks():
            print(
                "\t%s\t\tRSSI: %d\tChannel: %d"
                % (str(network.ssid, "utf-8"), network.rssi, network.channel)
            )
        wifi.radio.stop_scanning_networks()

        print("Connecting to %s" % secrets["ssid"])
        wifi.radio.connect(secrets["ssid"], secrets["password"])
        print("Connected to %s!" % secrets["ssid"])
        print("My IP address is", wifi.radio.ipv4_address)

        return socketpool.SocketPool(wifi.radio)


#
# This class obtains a request object from the socket pool which we
# will reuser since if we keep allocating request objects we run out
# over time.
#
class get_request:
    def __init__(self, requestPool):
        self.requestPool = requestPool
        self.needRequest = True

    def get_request_object(self):
        # Only setup the request object once
        if self.needRequest:
            print("allocating request from pool")
            self.requests = adafruit_requests.Session(
                self.requestPool, ssl.create_default_context()
            )
            self.needRequest = False
        return self.requests


class get_internet_time:
    def __init__(self, requestObject):
        self.requestObject = requestObject
        self.needRequest = True

    def get_local_time(self):
        JSON_TIME_URL = "http://worldtimeapi.org/api/ip"

        print("Fetching json from", JSON_TIME_URL)
        response = self.requestObject.get(JSON_TIME_URL)
        print("-" * 40)
        print(response.status_code)
        if response.status_code == 200:
            print(response.json())
            print("-" * 40)
            return response.json()
        return {"datetime": "time unavailable."}


#
# This class sends an HTTP rest style API PUT to Twilio to send_report
# and SMS messages.  You must have a Twilio account to use this code and
# place the Twilio from phone number, account id and auth token in the
# secrests file.
#
class TwilioSMS:
    base_url = "https://api.twilio.com/2010-04-01"

    #
    # The class init method defines the HTTP basic authorization string.
    # This string is in the format username:password base64 encoded
    #
    def __init__(self, requestPool, account_sid, auth_token):
        self.twilio_auth_token = auth_token
        self.twilio_account_sid = account_sid
        self.twilioAuthString = "{sid}:{token}".format(
            sid=account_sid, token=auth_token
        )

        # binascii requires a byte arrary instead of a string
        self.twilioAuthBytes = bytes(self.twilioAuthString, "utf-8")

        # HTTP Authorization requires a string so use decode to change it back.
        # the bsa_base64 method adds a LF on the end so use .strip to remove it
        self.twilio_auth = (
            binascii.b2a_base64(self.twilioAuthBytes).strip().decode("ascii")
        )

        self.requestObject = requestObject

    def create(self, body, from_, to):

        fromHTTP = from_.replace("+", "%2B")
        toHTTP = to.replace("+", "%2B")

        # The PUT data is formatted as JSON and the keywords are
        # required by Twilio
        payloadHTTP = {
            "Body": body,
            "To": toHTTP,
            "From": fromHTTP,
        }

        # Use HTTP basic authorization
        headersHTTP = {"Authorization": "Basic %s" % self.twilio_auth}
        print(self.twilio_auth)
        print("-- ")
        print(headersHTTP)

        r = self.requestObject.post(
            "https://api.twilio.com/2010-04-01/"
            + "Accounts/"
            + self.twilio_account_sid
            + "/Messages.json",
            data=payloadHTTP,
            headers=headersHTTP,
        )

        print("SMS sent with status code", r.status_code)
        print("Response: ", r.text)


def waiting_for_button():
    print("---------------------------------------------")
    print("************ Waiting for button *************")
    print("---------------------------------------------")


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


# -----------------------
# Main Code Starts Here
# -----------------------
#
myDot = dotstar()
myDot.off()

requestPool = connect_me.connect_wifi()
requestObject = get_request(requestPool).get_request_object()

# set up button
button_a = digitalio.DigitalInOut(board.D13)
button_a.direction = digitalio.Direction.INPUT
button_a.pull = digitalio.Pull.DOWN
cnt = 0

# Set up the Twilio REST API Call
sms = TwilioSMS(
    requestObject, secrets["TWILIO_ACCOUNT_SID"], secrets["TWILIO_AUTH_TOKEN"]
)

myDot.green()

waiting_for_button()

while True:
    if button_a.value:
        cnt += 1
        print("---------------------------------------------")
        print("Button Pressed: {}".format(cnt))
        # Turn dotstar red
        myDot.red()
        # Get the current time from the Internet
        getTime = get_internet_time(requestObject)
        # Split the time on a period and take the first part
        currentTime = getTime.get_local_time()["datetime"].split(".")[0]
        # Turn dotstar blue
        myDot.blue()
        # Send the SMS
        sms.create(
            body=secrets["message"] + ": " + currentTime,
            from_=secrets["TWILIO_FROM_NUMBER"],
            to=secrets["NOTIFICATION_NUMBER"],
        )
        waiting_for_button()
        myDot.green()
    time.sleep(0.1)

# We should never hit this code
print("done")  # Write your code here :-)
