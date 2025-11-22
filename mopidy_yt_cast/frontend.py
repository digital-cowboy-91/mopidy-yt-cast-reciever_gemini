import logging
import socket
import struct
import threading
import time
import pykka
from mopidy import core

logger = logging.getLogger(__name__)

SSDP_ADDR = '239.255.255.250'
SSDP_PORT = 1900
SSDP_MX = 1800
SSDP_ST = 'urn:dial-multiscreen-org:service:dial:1'

class SsdpResponder(threading.Thread):
    def __init__(self, port, uuid):
        super().__init__()
        self.daemon = True
        self.stopped = False
        self.port = port # Mopidy HTTP port
        self.uuid = uuid
        self.sock = None

    def get_ip(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            # doesn't even have to be reachable
            s.connect(('10.255.255.255', 1))
            IP = s.getsockname()[0]
        except Exception:
            IP = '127.0.0.1'
        finally:
            s.close()
        return IP

    def run(self):
        logger.info("Starting SSDP responder")
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        # Bind to the port
        try:
            self.sock.bind(('', SSDP_PORT))
        except Exception as e:
            logger.error(f"Could not bind to SSDP port {SSDP_PORT}: {e}")
            return

        # Join multicast group
        group = socket.inet_aton(SSDP_ADDR)
        mreq = struct.pack('4sL', group, socket.INADDR_ANY)
        self.sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

        while not self.stopped:
            try:
                data, addr = self.sock.recvfrom(1024)
                self.handle_request(data, addr)
            except Exception as e:
                if not self.stopped:
                    logger.error(f"SSDP error: {e}")

    def handle_request(self, data, addr):
        msg = data.decode('utf-8')
        if 'M-SEARCH' in msg and SSDP_ST in msg:
            logger.debug(f"Received SSDP M-SEARCH from {addr}")
            self.send_response(addr)

    def send_response(self, addr):
        ip = self.get_ip()
        location = f"http://{ip}:{self.port}/yt_cast/device-desc.xml"
        date_str = time.strftime('%a, %d %b %Y %H:%M:%S GMT', time.gmtime())
        
        response = f"""HTTP/1.1 200 OK\r
CACHE-CONTROL: max-age={SSDP_MX}\r
DATE: {date_str}\r
EXT:\r
LOCATION: {location}\r
SERVER: Linux/3.14 UPnP/1.0 Mopidy-Yt-Cast/0.1.0\r
ST: {SSDP_ST}\r
USN: {self.uuid}::{SSDP_ST}\r
BOOTID.UPNP.ORG: 1\r
CONFIGID.UPNP.ORG: 1\r
\r
"""
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.sendto(response.encode('utf-8'), addr)
        sock.close()

    def stop(self):
        self.stopped = True
        if self.sock:
            self.sock.close()

class YtCastFrontend(pykka.ThreadingActor, core.CoreListener):
    def __init__(self, config, core):
        super().__init__()
        self.config = config
        self.core = core
        self.ssdp = None
        # TODO: Get UUID from config or generate consistent one
        self.uuid = 'uuid:550e8400-e29b-41d4-a716-446655440000' 

    def on_start(self):
        http_port = self.config['http']['port']
        self.ssdp = SsdpResponder(http_port, self.uuid)
        self.ssdp.start()

    def on_stop(self):
        if self.ssdp:
            self.ssdp.stop()
