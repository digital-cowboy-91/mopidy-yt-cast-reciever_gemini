import socket
import struct

SSDP_ADDR = '239.255.255.250'
SSDP_PORT = 1900
SSDP_MX = 2
SSDP_ST = 'urn:dial-multiscreen-org:service:dial:1'

ssdpRequest = "M-SEARCH * HTTP/1.1\r\n" + \
              "HOST: {}:{}\r\n".format(SSDP_ADDR, SSDP_PORT) + \
              "MAN: \"ssdp:discover\"\r\n" + \
              "MX: {}\r\n".format(SSDP_MX) + \
              "ST: {}\r\n".format(SSDP_ST) + \
              "\r\n"

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.settimeout(5)

print("Sending SSDP M-SEARCH...")
sock.sendto(ssdpRequest.encode('utf-8'), (SSDP_ADDR, SSDP_PORT))

try:
    while True:
        data, addr = sock.recvfrom(1024)
        print(f"Received response from {addr}:")
        print(data.decode('utf-8'))
        # Keep listening
except socket.timeout:
    print("Timed out waiting for response.")
