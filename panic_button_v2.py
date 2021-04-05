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
# placed to Twilio and a text messages is sent.

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
#     }
#
# Note the telephone numbers must begin with a country code


import ipaddress
import ssl
import wifi
import socketpool
import adafruit_requests
import time
import board
import digitalio
import feathers2
import binascii
import struct
from adafruit_datetime import datetime

# Credit for this routine goes to Roland Smith post in StackOverflow Apr 21 '18
# It converts a Python sting to a Byte String
def rawbytes(s):
    """Convert a string to raw bytes without encoding"""
    outlist = []
    for cp in s:
        num = ord(cp)
        if num < 255:
            outlist.append(struct.pack("B", num))
        elif num < 65535:
            outlist.append(struct.pack(">H", num))
        else:
            b = (num & 0xFF0000) >> 16
            H = num & 0xFFFF
            outlist.append(struct.pack(">bH", b, H))
    return b"".join(outlist)


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

        ipv4 = ipaddress.ip_address("8.8.4.4")
        print("Ping google.com: %f ms" % (wifi.radio.ping(ipv4) * 5))

        return socketpool.SocketPool(wifi.radio)


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
        self.twilioAuthBytes = rawbytes(self.twilioAuthString)

        # HTTP Authorization requires a string so use decode to change it back.
        # the bsa_base64 method adds a LF on the end so use .strip to remove it
        self.twilio_auth = (
            binascii.b2a_base64(self.twilioAuthBytes).strip().decode("ascii")
        )

        self.requestPool = requestPool
        self.needRequest = True

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

        # Only setup the request object once
        if self.needRequest:
            self.requests = adafruit_requests.Session(
                self.requestPool, ssl.create_default_context()
            )
            self.needRequest = False

        # Use HTTP basic authorization
        headersHTTP = {"Authorization": "Basic %s" % self.twilio_auth}
        print(self.twilio_auth)
        print("-- ")
        print(headersHTTP)

        r = self.requests.post(
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


# -----------------------
# Main Code Starts Here
# -----------------------

requestPool = connect_me.connect_wifi()

# set up button
button_a = digitalio.DigitalInOut(board.D13)
button_a.direction = digitalio.Direction.INPUT
button_a.pull = digitalio.Pull.DOWN
cnt = 0

# Set up the Twilio REST API Call
sms = TwilioSMS(
    requestPool, secrets["TWILIO_ACCOUNT_SID"], secrets["TWILIO_AUTH_TOKEN"]
)

waiting_for_button()

while True:
    if button_a.value:
        cnt += 1
        print("---------------------------------------------")
        print("Button Pressed: {}".format(cnt))
        feathers2.led_set(True)
        # Send the SMS
        sms.create(
            body="Someone is at the door {}".format(datetime.now()),
            from_=secrets["TWILIO_FROM_NUMBER"],
            to=secrets["NOTIFICATION_NUMBER"],
        )
        waiting_for_button()
    time.sleep(0.1)
    feathers2.led_set(False)


# We should never hit this code
print("done")  # Write your code here :-)
