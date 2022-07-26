import sys
import network
import time
import machine
import ubinascii
import ujson
import neopixel # for blinky flashy thingy
from umqtt.simple import MQTTClient


wdt = machine.WDT()
CLIENT_ID = ubinascii.hexlify(machine.unique_id())
np = neopixel.NeoPixel(machine.Pin(0), 50)

def np_write_wrapper():
    wdt.feed()
    np.write()

default = []
fade_i = 0

for i in range(9): default.append((255, 0, 24))
for i in range(8): default.append((255, 165, 44))
for i in range(8): default.append((255, 255, 65))
for i in range(8): default.append((0, 128, 24))
for i in range(8): default.append((0, 0, 249))
for i in range(9): default.append((134, 0, 125))

def fail(e):
    print(e)
    print("** machine.reset() in 5 sec **")
    time.sleep(5)
    machine.reset()




def standard(np):
    for i in range(np.n):
        np[i] = default[i]
    np_write_wrapper()

def apply_colors(m):
   for i in range(np.n):
       try:
           t=m[i]
           np[i]=t
           default[i]=t
       except IndexError:
           pass
   np_write_wrapper()


def flash(c=(255,255,255),times=4):
  for i in range(times * np.n):
      for j in range(np.n):
          np[j] = (0, 0, 0)
          np[i % np.n] = c
      np_write_wrapper()
  time.sleep_ms(10)
  apply_colors(default)

def bounce():
    for i in range(4 * np.n):
        for j in range(np.n):
            np[j] = (0, 0, 128)
        if (i // np.n) % 2 == 0:
            np[i % np.n] = (0, 0, 0)
        else:
            np[np.n - 1 - (i % np.n)] = (0, 0, 0)
        np_write_wrapper()
        time.sleep_ms(60)

def blink():
  for i in range(0, 4 * 256, 8):
    for j in range(np.n):
        if (i // 256) % 2 == 0:
            val = i & 0xff
        else:
            val = 255 - (i & 0xff)
        np[j] = (val, 0, 0)
    np_write_wrapper()
  apply_colors(default)

def fade_one(i):
    n = np.n
    for j in range(n):
        val = i
        d = default[j]
        np[j] = (int(d[0] * (val/255)), int(d[1] * (val/255)),  int(d[2] * (val/255)))
        np_write_wrapper()

def on_receive(t, m):
    print("Onreceive")
    global fade_going
    fade_going=False
    flash(times=1)
    blink()
    flash(times=1)
    fade_going=True

def main():
    with open('farnsworth.json') as fp:
        config = ujson.loads(fp.read())

    standard(np)

    ap_if = network.WLAN(network.AP_IF)
    if ap_if.active():
        ap_if.active(False)

    print("Station active")
    station = network.WLAN(network.STA_IF)
    station.active(True)
    station.connect(config['wifi']['ssid'],config['wifi']['psk'])

    while not station.isconnected():
        machine.idle()

    print("Connected wifi")

    while True:
        c = MQTTClient(client_id = CLIENT_ID,
                       server     = config['mqtt']['server'],
                       user       = config['mqtt']['user'],
                       password   = config['mqtt']['password'],
                       port       = config['mqtt']['port'],
                       ssl        = config['mqtt']['ssl']
        )
        c.set_callback(on_receive)
        print("Connecting to mqtt")
        wdt.feed()
        c.connect()
        wdt.feed()
        print("Subscribing to topic")
        c.subscribe(config['mqtt']['topic'])
        print("Entering wait_msg loop")
        while True:
            c.check_msg()
            wdt.feed()

try:
    main()
except Exception as e:
    fail(e)
