import sys
import platform
import asyncio
import time
from bleak import BleakScanner, BleakClient
import io
import os
from pathlib import Path
from collections import defaultdict
import json

from BTLegoMario import BTLegoMario

mario_devices = {}
callbacks_to_device_addresses = {}
code_data = None

json_code_file = "mariocodes.json"
run_seconds = 600

volume = 0

coin_counts = defaultdict(lambda: defaultdict(int))
names = {}

async def mariocallbacks(message):
        # ( type, key, value )
        global volume

        print("CALLBACK:"+str(message))
        mario_device = mario_devices[callbacks_to_device_addresses[message[0]]]
        print(message[1:])
        if message[1:] == ("info", "brother", "mario"):
            names[mario_device] = message[3]
            os.system(f"say hello mario")
        if message[1:] == ("info", "brother", "luigi"):
            names[mario_device] = message[3]
            os.system(f"say hello luigi")
        if message[1:] == ("info", "brother", "peach"):
            names[mario_device] = message[3]
            os.system(f"say hello peach")

        if message[1:-1] == ('event', 'coincount'):
            coin_counts[mario_device][message[3][1]] = message[3][0]
            print(coin_counts[mario_device])
            total = sum(coin_counts[mario_device].values())
            os.system(f"say {total} coins for {names[mario_device]}")

async def detect_device_callback(device, advertisement_data):
        global mario_devices
        global callbacks_to_device_addresses
        global code_data

        if device:
                mario_device = BTLegoMario.which_device(advertisement_data)
                if mario_device:
                        if not device.address in mario_devices:
                                mario_devices[device.address] = BTLegoMario(code_data)
                                callback_uuid = mario_devices[device.address].register_callback(mariocallbacks)
                                callbacks_to_device_addresses[callback_uuid] = device.address
                                await mario_devices[device.address].subscribe_to_messages_on_callback(callback_uuid, 'event')
                                await mario_devices[device.address].subscribe_to_messages_on_callback(callback_uuid, 'pants')
                                await mario_devices[device.address].subscribe_to_messages_on_callback(callback_uuid, 'motion')
                                await mario_devices[device.address].subscribe_to_messages_on_callback(callback_uuid, 'gesture')
                                await mario_devices[device.address].subscribe_to_messages_on_callback(callback_uuid, 'info')
                                await mario_devices[device.address].subscribe_to_messages_on_callback(callback_uuid, 'error')
                                await mario_devices[device.address].subscribe_to_messages_on_callback(callback_uuid, 'scanner', True)

                                await mario_devices[device.address].connect(device, advertisement_data)
                        else:
                                if not mario_devices[device.address].connected:
                                        await mario_devices[device.address].connect(device, advertisement_data)
                                else:
                                        print("Refusing to reconnect to "+mario_devices[device.address].which_brother)
                else:
                        # "LEGO Mario_x_y"
                        # Spike prime hub starts with "LEGO Hub" but you have to pair with that, not BTLE
                        if device.name and device.name.startswith("LEGO Mario"):
                                if advertisement_data and advertisement_data.manufacturer_data:
                                        print("UNKNOWN LEGO MARIO",mario_device, device.address, "RSSI:", device.rssi, advertisement_data)
                                else:
                                        #print("Found some useless Mario broadcast without the manufacturer or service UUIDs")
                                        pass

async def callbackscan(duration=10):
        scanner = BleakScanner()
        print("Ready to find LEGO Mario!")
        scanner.register_detection_callback(detect_device_callback)
        print("Scanning...")
        await scanner.start()
        await asyncio.sleep(duration)
        await scanner.stop()

        #print("Scan results...")
        #for d in scanner.discovered_devices:
        #        print(d)

check_file = Path(os.path.expanduser(json_code_file))
if check_file.is_file():
        with open(check_file, "rb") as f:
                try:
                        code_data = json.loads(f.read())
                except ValueError as e:  # also JSONDecodeError
                        print("Unable to load code translation JSON:"+str(e))

if not code_data:
        print("Known code database (mariocodes.json) NOT loaded!")

try:
        asyncio.run(callbackscan(run_seconds))
except KeyboardInterrupt:
        print("Recieved keyboard interrupt, stopping.")

if len(mario_devices):
        print("Done with LEGO Mario session after "+str(run_seconds)+" seconds...")
else:
        print("Didn't connect to a LEGO Mario.  Quitting.")
