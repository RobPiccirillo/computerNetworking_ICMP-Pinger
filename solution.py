import statistics
from socket import *
import os
import sys
import struct
import time
import select
import binascii
# Should use stdev

ICMP_ECHO_REQUEST = 8


def checksum(string):
    csum = 0
    countTo = (len(string) // 2) * 2
    count = 0

    while count < countTo:
        thisVal = (string[count + 1]) * 256 + (string[count])
        csum += thisVal
        csum &= 0xffffffff
        count += 2

    if countTo < len(string):
        csum += (string[len(string) - 1])
        csum &= 0xffffffff

    csum = (csum >> 16) + (csum & 0xffff)
    csum = csum + (csum >> 16)
    answer = ~csum
    answer = answer & 0xffff
    answer = answer >> 8 | (answer << 8 & 0xff00)
    return answer



def receiveOnePing(mySocket, ID, timeout, destAddr):
    timeLeft = timeout
    global roundTrip_min, roundTrip_max, roundTrip_count, roundTrip_sum, roundTrip_stdevList

    while 1:
        startedSelect = time.time()
        whatReady = select.select([mySocket], [], [], timeLeft)
        howLongInSelect = (time.time() - startedSelect)
        if whatReady[0] == []:  # Timeout
            return "Request timed out."

        timeReceived = time.time()
        recPacket, addr = mySocket.recvfrom(1024)

        # Fill in start
        
        # Fetch the ICMP header from the IP packet
        icmpHeader = recPacket[20:28]
        icmpType, code, checksum, pID, sequence = struct.unpack("bbHHh", icmpHeader)
        print("ICMP Header: ", icmpType, code, checksum, pID, sequence)
        roundTrip = 0

        if pID != ID: #& icmpType != 8:
            return 'Expected type=0'

        bytesToDouble = struct.calcsize("d")
        timeTo = struct.unpack("d", recPacket[28:28 + bytesToDouble])[0]
        roundTrip = (timeReceived - timeTo)*1000

        roundTrip_min = min(roundTrip_min, roundTrip)
        roundTrip_max = max(roundTrip_max, roundTrip)
        roundTrip_count += 1
        roundTrip_sum += roundTrip
        roundTrip_stdevList.append(roundTrip)
        print("RTT Count:", roundTrip_count)
        print("RTT Min:", roundTrip_min)
        print("RTT Max:", roundTrip_max)

        return roundTrip


        # Fill in end
        timeLeft = timeLeft - howLongInSelect
        if timeLeft <= 0:
            return "Request timed out."


def sendOnePing(mySocket, destAddr, ID):
    # Header is type (8), code (8), checksum (16), id (16), sequence (16)

    myChecksum = 0
    # Make a dummy header with a 0 checksum
    # struct -- Interpret strings as packed binary data
    header = struct.pack("bbHHh", ICMP_ECHO_REQUEST, 0, myChecksum, ID, 1)
    data = struct.pack("d", time.time())
    # Calculate the checksum on the data and the dummy header.
    myChecksum = checksum(header + data)

    # Get the right checksum, and put in the header

    if sys.platform == 'darwin':
        # Convert 16-bit integers from host to network  byte order
        myChecksum = htons(myChecksum) & 0xffff
    else:
        myChecksum = htons(myChecksum)


    header = struct.pack("bbHHh", ICMP_ECHO_REQUEST, 0, myChecksum, ID, 1)
    packet = header + data

    mySocket.sendto(packet, (destAddr, 1))  # AF_INET address must be tuple, not str


    # Both LISTS and TUPLES consist of a number of objects
    # which can be referenced by their position number within the object.

def doOnePing(destAddr, timeout):
    icmp = getprotobyname("icmp")


    # SOCK_RAW is a powerful socket type. For more details:   http://sockraw.org/papers/sock_raw
    mySocket = socket(AF_INET, SOCK_RAW, icmp)

    myID = os.getpid() & 0xFFFF  # Return the current process i
    sendOnePing(mySocket, destAddr, myID)
    delay = receiveOnePing(mySocket, myID, timeout, destAddr)
    mySocket.close()
    return delay


def ping(host, timeout=1):
    global roundTrip_count, roundTrip_sum, roundTrip_min, roundTrip_max, roundTrip_stdevList
    roundTrip_min = float('+inf')
    roundTrip_max = float('-inf')
    roundTrip_count = 0
    roundTrip_sum = 0
    roundTrip_stdevList = []
    count = 0
    # timeout=1 means: If one second goes by without a reply from the server,  	# the client assumes that either the client's ping or the server's pong is lost
    dest = gethostbyname(host)
    print("Pinging " + dest + " using Python:")
    print("")
    # Calculate vars values and return them
    #if count != 0:
    #    packet_avg = roundTrip_sum / roundTrip_count
    #    vars = [str(round(packet_min, 2)), str(round(packet_avg, 2)), str(round(packet_max, 2)),str(round(stdev(stdev_var), 2))]
    #else:
    #    vars = []
    #    packet_avg = 0
    # Send ping requests to a server separated by approximately one second
    for i in range(0,4):
        delay = doOnePing(dest, timeout)
        count += 1
        packet_min = roundTrip_min
        packet_max = roundTrip_max
        stdev_var = roundTrip_stdevList        
        print(delay)
        time.sleep(1)  # one second

    if count != 0:
        packet_avg = roundTrip_sum / roundTrip_count
        vars = [str(round(packet_min, 4)), str(round(packet_avg, 4)), str(round(packet_max, 4)),str(round(statistics.stdev(stdev_var), 4))]
    else:
        vars = []
        packet_avg = 0
        
    #print(vars)
    #if vars == []:
    #    print("No vars")
    return vars

if __name__ == '__main__':
    ping("google.co.il")
