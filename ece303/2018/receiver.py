# Written by S. Mevawala, modified by D. Gitzel
import time
import logging
import struct
import string
import zlib
import channelsimulator
import utils
import sys
import socket

class Receiver(object):

    def __init__(self, inbound_port=50005, outbound_port=50006, timeout=0.9, debug_level=logging.INFO):
        self.logger = utils.Logger(self.__class__.__name__, debug_level)

        self.inbound_port = inbound_port
        self.outbound_port = outbound_port
        self.simulator = channelsimulator.ChannelSimulator(inbound_port=inbound_port, outbound_port=outbound_port,
                                                           debug_level=debug_level)
        self.simulator.rcvr_setup(timeout)
        self.simulator.sndr_setup(timeout)

    def checksum(self,seqNum,data):
        filled_Data = string.join([string.zfill(n,8) for n in map(lambda s: s[2:], map(bin, data))], '')
        checksum = zlib.adler32(seqNum + filled_Data) & 0xffffffff
        return checksum

    def receive(self):
        self.logger.info("Receiving on port: {} and replying with ACK on port: {}".format(self.inbound_port, self.outbound_port))

        lower = 0
        WINDOW = 128
        terminate = False
        received_packets = {}
        while not terminate:
            try:
                data = self.simulator.u_receive()  # receive data

                if data[0] & (~data[1] & 0xFF) & data[2] & data[3] & data[4] & data[5] & data[6] == 255:
                    self.simulator.u_send(bytearray([255, 0] + [255]*5))
                    terminate = True

                #deconstruct the data into relevant portions
                rcv_seqNum =data[0:4]
                rcv_binary_iterator = bin(struct.unpack(">i",rcv_seqNum)[0])[2:].zfill(32)
                rcv_length = data[4:8]
                rcv_checksum = data[8:12]
                rcv_data = data[12:]
                #print rcv_data
                self.logger.info('rcved {}'.format(struct.unpack(">i", rcv_seqNum)[0]))

                #at this point, we have received and deconstructed the message

                #verify the checksum 
                rcv_checksum_string = bin(self.checksum(rcv_binary_iterator, rcv_data))
                checksum = bytearray(int(rcv_checksum_string[i:i+8],2) for i in range(0,32,8))
                
                if checksum == rcv_checksum:
                    #store message 
                    received_packets[struct.unpack(">i",rcv_seqNum)[0]] = rcv_data[:struct.unpack(">i", rcv_length)[0]]
                    
                    #send back ACK
                    #send back burst of 1111 or 0000. No need to checksum, as the probability of error on flipping all four bits from 
                    # 1111 -> 0000 is highly improbable
                    ones = 1111
                    msg = rcv_seqNum + struct.pack(">i",ones)
                    self.simulator.u_send(msg)
                    self.logger.info('ack is sent back {}'.format(struct.unpack(">i", rcv_seqNum)[0]))
                    #print('ack is sent back', struct.unpack(">i", rcv_seqNum)[0])
                else:
                    #send back NAK (doesn't really matter, is ignored anyways)
                    zeros = 0000
                    msg = rcv_seqNum + struct.pack(">i",zeros)
                    self.simulator.u_send(msg)
                    #self.logger.info('nack is sent back {}'.format(struct.unpack(">i", rcv_seqNum)[0]))
                    #print('nack is sent back', struct.unpack(">i", rcv_seqNum)[0])

            except Exception as e:
                self.logger.info(str(e))
                pass

        #write the packets out
        self.logger.info('writing to output file')
        for key,value in sorted(received_packets.items()):
            sys.stdout.write(value)

        sys.exit()
        

if __name__ == "__main__":
    rcvr = Receiver()
    rcvr.receive()
