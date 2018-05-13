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

    def __init__(self, inbound_port=50005, outbound_port=50006, timeout=10, debug_level=logging.INFO):
        self.logger = utils.Logger(self.__class__.__name__, debug_level)

        self.inbound_port = inbound_port
        self.outbound_port = outbound_port
        self.simulator = channelsimulator.ChannelSimulator(inbound_port=inbound_port, outbound_port=outbound_port,
                                                           debug_level=debug_level)
        self.simulator.rcvr_setup(timeout)
        self.simulator.sndr_setup(timeout/5)


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
        while True:
            try:
                data = self.simulator.u_receive()  # receive data


                if data[0] & (~data[1] & 0xFF) & data[2] & data[3] & data[4] & data[5] & data[6] == 255:
                    self.simulator.u_send(bytearray([255, 0] + [255]*5))
                    terminate = True

                #deconstruct the data into relevant portions
                rcv_seqNum =data[0:4]
                rcv_binary_iterator = bin(struct.unpack(">i",rcv_seqNum)[0])[2:].zfill(32)
                #print rcv_binary_iterator
                #print type(rcv_binary_iterator)
                rcv_length = data[4:8]
                rcv_checksum = data[8:12]
                rcv_data = data[12:]
                #print rcv_data

                '''
                print '-----------------------------------'
                print ('data received is: ', str(data[:]))
                print 'rcv_seqNum is: ', struct.unpack(">i",rcv_seqNum)[0]
                print 'length is: ', struct.unpack(">i",rcv_length)[0]
                print 'checksum is: ', struct.unpack(">i", rcv_checksum)[0]
                print 'message is: ', rcv_data
                '''
                #at this point, we have received and deconstructed the message
                #print 'message is: ', rcv_data

                #verify the checksum 
                rcv_checksum_string = bin(self.checksum(rcv_binary_iterator, rcv_data)).zfill(32)
                checksum = bytearray(int(rcv_checksum_string[i:i+8],2) for i in range(0,32,8))
        
                if checksum == rcv_checksum:
                    #store message 
                    received_packets[struct.unpack(">i",rcv_seqNum)[0]] = rcv_data
                    '''
                    lowerSeqNum = lower
                    #print lowerSeqNum
                    upperSeqNum = lower + WINDOW
                    #print upperSeqNum
                    diff = (rcv_SeqNum - lowerSeqNum)
                    #print diff
        
                    if ((upperSeqNum - lowerSeqNum > 0 and rcv_seqNum >= lowerSeqNum and rcv_seqNum <= upperSeqNum ) or (upperSeqNum - lowerSeqNum) < 0 and (rcv_seqNum >=lowerSeqNum or rcv_seqNum <= upperSeqNum)):
                        if lower + diff >= len(received_packets):
                            received_packets += [None] *8192
                        if received_packets[lower + diff]==None:
                            received_packets[lower + diff] = rcv_data
                    '''
                    #send back ACK
                    ones = 1111
                    msg = rcv_seqNum + struct.pack(">i",ones)
                    self.simulator.u_send(msg)
                    #print 'ack is sent back', struct.unpack(">i", rcv_seqNum)[0]
                else:
                    #send back NAK
                    zeros = 0000
                    msg = rcv_seqNum + struct.pack(">i",zeros)
                    self.simulator.u_send(msg)
                    #print 'nak'

                '''
                if diff == 0:
                    for i in range (lower, len(received_packets)):
                            if received_packets[i] == None:
                                lower = i
                                break
                '''
                
            except:
                if terminate:
                    break
                else:
                    pass
                    ''' 
                    #send back NAK
                    zeros = 0000
                    msg = rcv_seqNum + struct.pack(">i",zeros)
                    self.simulator.u_send(msg)
                    #print 'nak'
                    '''
        #write the packets out
        for key,value in sorted(received_packets.items()):
            sys.stdout.write(value)


        sys.exit()
        

if __name__ == "__main__":
    #test out Receiver
    #rcvr = Receiver()
    #rcvr.receive()

    # test out BogoReceiver
    rcvr = Receiver()
    rcvr.receive()
