from ppadb.client import Client as AdbClient

class ADBManager:
    def __init__(self, host="127.0.0.1", port=5037):
        self.client = AdbClient(host=host, port=port)
        self.devices = {}
        
    def get_device(self, identifier=None):
        # identifier could be IP:PORT for wireless ADB
        devices = self.client.devices()
        if not devices:
            print("No ADB devices connected.")
            return None
        
        if identifier:
            for dev in devices:
                if identifier in dev.serial:
                    return dev
        
        # Return first device if no specific one requested
        return devices[0]

    def connect_wireless(self, ip: str, port: int = 5555):
        try:
            self.client.remote_connect(ip, port)
            print(f"Connected to {ip}:{port} wirelessly.")
            return True
        except Exception as e:
            print(f"Failed to connect to {ip}:{port}: {e}")
            return False
