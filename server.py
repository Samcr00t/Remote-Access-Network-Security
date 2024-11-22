import asyncio
import websockets
import time
import subprocess


def create_file():
    filename = "result.txt"
    filename1 = "known_ip.txt"
    open(filename, 'w').close()
    open(filename1, 'w').close() 
    return filename, filename1


def extract_device_names(filename):
    device_names = []
    with open(filename, 'r') as file:
        lines = file.readlines()
        device_names = [line.strip() for line in lines]
    return device_names


async def check_new_devices(device_names, filename1, websocket):
    with open(filename1, 'r+') as f:
        known_devices = [line.strip() for line in f.readlines()]  
        new_devices = [device for device in device_names if device not in known_devices]
        
        
        for device in new_devices:
            
            await websocket.send(f"A foreign device has been detected: {device}\nTo add to recognized devices, type 1\nTo ignore, type 2")
            
            
            choice = await websocket.recv()
            if choice == '1':
                f.write(device + '\n')  
                f.flush()  
            elif choice == '2':
                print(f"Device {device} ignored by the client.")


async def run_scan(filename, stop_event):
    while not stop_event.is_set():
        
        result = subprocess.run(['fping', '-a', '-g', '192.168.1.0/24'], stdout=subprocess.PIPE, text=True, stderr=subprocess.PIPE)
        
        
        if result.stderr:
            pass
        
        
        with open(filename, 'a') as f:
            f.write(result.stdout)
        
        await asyncio.sleep(60)


async def handle_client(websocket, path):
    print("Client connected!")
    
    filename, filename1 = create_file()  
    stop_event = asyncio.Event()

    
    asyncio.create_task(run_scan(filename, stop_event))
    
    try:
        while True:
            
            device_names = extract_device_names(filename)
            
            await check_new_devices(device_names, filename1, websocket)
            
            await asyncio.sleep(60) 
    except websockets.exceptions.ConnectionClosed:
        print("Client disconnected.")
    finally:
        stop_event.set()  
        print("Scanning stopped.")


start_server = websockets.serve(handle_client, '0.0.0.0', 8765)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()
