# Written by S. Mevawala, modified by D. Gitzel
import time
import struct
import string
import logging
import socket
import zlib
import channelsimulator
import utils
import sys
import binascii

class Sender(object):
    #selective repeat
    WINDOW = 128 
    #MAX_SEQ_NO = 4294967296 #2^32
    PACKET_DATA_BYTES = 64

    def __init__(self, inbound_port=50006, outbound_port=50005, timeout=0.9, debug_level=logging.INFO):
        self.logger = utils.Logger(self.__class__.__name__, debug_level)

        self.inbound_port = inbound_port
        self.outbound_port = outbound_port
        self.simulator = channelsimulator.ChannelSimulator(inbound_port=inbound_port, outbound_port=outbound_port,
                                                           debug_level=debug_level)
        self.simulator.sndr_setup(timeout)
        self.simulator.rcvr_setup(timeout)
    

    def checksum(self, seqNum,data):
        filled_Data = string.join([string.zfill(n, 8) for n in map(lambda s: s[2:], map(bin, data))], '')
        checksum = zlib.adler32(seqNum + filled_Data) & 0xffffffff
        return checksum

    #parse the input for all metadata and data
    def data_split(self, data):
        data_array = []
        dictionary = {}
        iterator = 0
        for i in range(0,len(data), self.PACKET_DATA_BYTES):
            #i is current byte iterator
            upper = i + self.PACKET_DATA_BYTES
            if upper > len(data):
                upper = len(data)
            #length_of_data = bytearray([(upper - i) & 0xff]) #0xff = 255
            length_of_data = struct.pack(">i",(upper-i) & 0xFF) 
            #print length_of_data
            #print 'length of data is: ' , struct.unpack(">i",length_of_data)[0]

            binary_iterator = "{0:b}".format(iterator).zfill(32)
            sequence_no = bytearray(int(binary_iterator[i:i+8],2) for i in range(0,32,8))
            #print binary_iterator
            #print type(binary_iterator)
            #print ('sequence number is:', str(sequence_no[0:4]))
             
            data_packet = data[i:upper] + bytearray([0]*(self.PACKET_DATA_BYTES + i - upper))
            #print 'data packet is:', data_packet

            
            checksum_string = bin(self.checksum(binary_iterator, data_packet))#.zfill(32)
            print (checksum_string)
            checksum = bytearray(int(checksum_string[i:i+8],2) for i in range(0,32,8)) 
            #print checksum_string
            #print ('sequence number is:'+ str(checksum[0:4]))

            #create the 4 tuple #make sure these are all byte arrays
            data_array.append({
                "seqNum":sequence_no,
                "length":length_of_data,
                "checksum":checksum,
                "data":data_packet,
                "sent":False
                #"ack":False,
                })
            dictionary[iterator] = False
            iterator+=1 
        return data_array, dictionary



    def send(self, data):
        #send the data tuple-at-a-time
        #can compare the ACKs with the list of tuples
        data_array, dictionary = self.data_split(data)
        num_of_packets = len(data_array) #0-1542 in test case
    
        window_size = self.WINDOW 
        lower = 0

        sn_lower_bound = 0
        sn_upper_bound = 0

        if num_of_packets < window_size:
            window_size = num_of_packets
         
        while True:
            try:
                upper = lower + window_size
                
                if upper > num_of_packets:
                    upper = num_of_packets
                    
                #find sequence numbers in pertaining window
                #in data_array form
                sn_lb = data_array[lower]["seqNum"]
                sn_ub = data_array[upper-1]["seqNum"]
                #print ('lower bound is: ', str(sn_lb[0:4]))
                #print ('upper bound is: ', str(sn_ub[0:4]))
                #in integer form
                sn_lower_bound = struct.unpack(">i",data_array[lower]["seqNum"])[0]
                sn_upper_bound = struct.unpack(">i",data_array[upper-1]["seqNum"])[0]
                #print sn_lower_bound, sn_upper_bound

                #send the packets in window
                for i in range(sn_lower_bound,sn_upper_bound+1):
                    if data_array[i]["sent"] == False:
                        datagram = data_array[i]["seqNum"] +  data_array[i]["length"] + data_array[i]["checksum"] + data_array[i]["data"]
                        ''' 
                        print ('seqNum is:',str(data_array[i]["seqNum"][:]))
                        #print 'length of data is: ' , struct.unpack(">i",data_array[i]["length"])[0]
                        print ('length is:', data_array[i]["length"])
                        print ('checksum is:',str(data_array[i]["checksum"][:]))
                        print ('data is:',str(data_array[i]["data"][:]))
                        print ('datagram is:',str(datagram[:]))
                        '''
                        self.simulator.u_send(datagram)  # send data
                        self.logger.info('sent {} of {} packets'.format(i+1, num_of_packets))

                        data_array[i]["sent"] = True
                
                while True: #ack stuff
                    ack = self.simulator.u_receive() 
                    
                    ack_seqNum = ack[0:4]
                    integer = struct.unpack(">i",ack_seqNum)[0]
                    #self.logger.info('received ack for {}'.format(integer))
                    ack_data = ack[4:8]
                    output= struct.unpack(">i",ack_data)[0]
                    
                    if (output == 1111 or output == 1110 or output == 1101 or output== 1011 or output== 0111) and integer >= lower and integer <= upper and dictionary[integer] == False:
                        data_array[integer]["ack"] = True
                        dictionary[integer] = True
                        if integer == lower:
                            break
                    '''
                    #program struggles near edge of window range. Thus, when it gets close to the window range, it's forced to go back and continue calculations                   
                    if integer == (upper-2):
                        for i in range(sn_lower_bound,sn_upper_bound):
                            if not dictionary[i]:
                                datagram = data_array[i]["seqNum"] +  data_array[i]["length"] + data_array[i]["checksum"] + data_array[i]["data"]
                                self.simulator.u_send(datagram)  # send data
                    '''
                    datagram = data_array[num_of_packets-1]["seqNum"] +  data_array[num_of_packets -1]["length"] + data_array[num_of_packets-1]["checksum"] + data_array[num_of_packets-1]["data"]
                    self.simulator.u_send(datagram)  # send data
                       
                #update lower bound on window
                tempLower = lower
                for i in range(lower,upper+1):
                    if not dictionary[i]:
                        lower = i
                        break
                    
                if lower == num_of_packets-self.WINDOW+1:  #everything has been acked
                    print 'finished'
                    break

           #timeout, keep sending data 
            except socket.timeout as e:
                self.logger.info(str(e))
                self.logger.debug('lower: {};\nupper: {}\n'.format(sn_lower_bound, sn_upper_bound))
                for i in range(sn_lower_bound,sn_upper_bound+1):
                    if not dictionary[i]:
                        self.logger.info('sending {} of {} packets'.format(i+1, num_of_packets))
                        print('sending {} of {} packets'.format(i+1, num_of_packets))
                        datagram = data_array[i]["seqNum"] +  data_array[i]["length"] + data_array[i]["checksum"] + data_array[i]["data"]
                        self.simulator.u_send(datagram)  # send data
                        self.logger.info('sent {} of {} packets'.format(i+1, num_of_packets))

                for i in range(sn_lower_bound,sn_upper_bound+1):
                    if not dictionary[i]:
                        lower = i
                        break

            ##send end transmission packet
        while True:
            self.simulator.u_send(bytearray([255, 0] + [255]*5))
            # check for end transmission
            try:
                ack = self.simulator.u_receive()
            except socket.timeout as e:
                self.logger.info(str(e))
                sys.exit()
            if ack[0] & (~ack[1] & 0xFF) & ack[2] & ack[3] & ack[4] & ack[5] & ack[6] == 255:
                break
        sys.exit()


if __name__ == "__main__":
    #due to the inconsistencies in the makefile, I added this
    #time.sleep() to mitigate potential race conditions
    #actual program time is therefore 0.1 seconds faster :)
    time.sleep(0.1)
    
    DATA = bytearray(sys.stdin.read())
    sndr = Sender()
    z = sndr.send(DATA)
    #print(z)

    
