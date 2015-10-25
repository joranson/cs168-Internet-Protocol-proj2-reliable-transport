import sys
import getopt
import random

import Checksum
import BasicSender

'''
This is a skeleton sender class. Create a fantastic transport protocol here.
'''
class Sender(BasicSender.BasicSender):
    def __init__(self, dest, port, filename, debug=False, sackMode=False):
        super(Sender, self).__init__(dest, port, filename, debug)
        self.sackMode = sackMode
        self.debug = debug

    # Main sending loop.
    def start(self):
        sequence_num_size = 2**32
        sequence_num = random.randint(1, 2**32-1)
        window_size = 7
        window = []
        block_size = 1400

        syn = self.make_packet("syn", sequence_num, "")
        sequence_num = (sequence_num + 1) % sequence_num_size
        if self.debug:
            print ">>>", syn
        self.send(syn)
        res = self.receive(0.5)
        while not res or not Checksum.validate_checksum(res):   ## need to check if syn is received by receiver or corrupted
            if self.debug:
                print "<<< RESEND SYN: ", res
            self.send(syn)
            res = self.receive(0.5)
        if self.debug:
            print "<<< GOT VALID ACK FROM RECV: ", self._split_message(res)

        next_send_seq = sequence_num-1
        END = False

        # Used to determine the exact packets to send in SACK Mode
        lastAckPacket = None

        lastAckSqn = None
        sameAckCount = 0

        while True:
            if self.debug:
                print "now window size--------> ", len(window)
            while len(window)<7:
                data = self.infile.read(block_size)
                if not data and END:        # second time tring to get EOF, don't append to window
                    break
                if not data:
                    fin = self.make_packet("fin", sequence_num, data)
                    if self.debug:
                        print ">>> EOF ", fin
                    window.append((sequence_num,fin))
                    sequence_num = (sequence_num + 1) % sequence_num_size
                    END = True
                    break
                data_packet = self.make_packet("dat", sequence_num, data)
                window.append((sequence_num,data_packet))
                sequence_num = (sequence_num + 1) % sequence_num_size
            for d in window:
                if d[0]> next_send_seq:        # only send those haven't been sent
                    self.send(d[1])
                    if self.debug:
                        print ">>> SEND WINDOW with SEQUENCE ######## ", d[0]
            if self.debug:
                print "------------------------ ONE WINDOW SENT ----------------------- "
            res = self.receive(0.5)

            if res and Checksum.validate_checksum(res):             # if sender not receving any ack, this will continue to next loop and send the whole window again
                
                lastAckPacket = res
                # print "received sth", lastAckPacket

                if sackMode:
                    expected_next_seq = long(((self._split_message(res)[1]).split(';'))[0])     # if sender receives some ack, this will move the window
                else:
                    expected_next_seq = long(self._split_message(res)[1])

                # Retransmit upon receiving more than 3 identical acks.
                if lastAckSqn == expected_next_seq:
                    sameAckCount += 1
                    if sameAckCount >= 4:
                        if sackMode:
                            #Delete received packets from window.
                            sack_msg = (self.split_packet(res)[1]).split(';')
                            msg_to_send = {}

                            for i in range(7):
                                msg_to_send[long(sack_msg[0])+i] = 1
                            for i in sack_msg[1]:
                                msg_to_send.pop(long(i))

                            for packet in window:
                                if packet[0] in msg_to_send:
                                    self.send(packet[1])

                    
                        self.send(window[0][1])
                else:
                    lastAckSqn = expected_next_seq
                    sameAckCount = 0

                new_window = []
                for d in window:
                    # print "*****************",  d[0]>=expected_next_seq
                    if d[0] >= expected_next_seq:
                        new_window.append(d)
                window = new_window
                if window!=[]:
                    next_send_seq = window[-1][0]
                if self.debug:
                    print "<<< RECEIVE ACK: ", res
            else:
                if not sackMode or not lastAckPacket:
                    next_send_seq = window[0][0]-1        # when no acks recevied on sender side, reset expected_next_seq to send the whole window
                else:
                    #Delete received packets from window.
                    sack_msg = (self.split_packet(lastAckPacket)[1]).split(';')
                    msg_to_send = {}

                    for i in range(7):
                        msg_to_send[long(sack_msg[0])+i] = 1
                    if sack_msg[1] != '':
                        for i in sack_msg[1].split(','):
                            msg_to_send.pop(long(i))

                    for packet in window:
                        if packet[0] in msg_to_send:
                            self.send(packet[1])

            if END and window==[]:
                break
        sys.exit()

    def _split_message(self, message):
        pieces = message.split('|')
        msg_type, seqno = pieces[0:2] # first two elements always treated as msg type and seqno
        checksum = pieces[-1] # last is always treated as checksum
        # data = '|'.join(pieces[2:-1]) # everything in between is considered data
        return msg_type, seqno, checksum


        
'''
This will be run if you run this script from the command line. You should not
change any of this; the grader may rely on the behavior here to test your
submission.
'''
if __name__ == "__main__":
    def usage():
        print "BEARS-TP Sender"
        print "-f FILE | --file=FILE The file to transfer; if empty reads from STDIN"
        print "-p PORT | --port=PORT The destination port, defaults to 33122"
        print "-a ADDRESS | --address=ADDRESS The receiver address or hostname, defaults to localhost"
        print "-d | --debug Print debug messages"
        print "-h | --help Print this usage message"
        print "-k | --sack Enable selective acknowledgement mode"

    try:
        opts, args = getopt.getopt(sys.argv[1:],
                               "f:p:a:dk", ["file=", "port=", "address=", "debug=", "sack="])
    except:
        usage()
        exit()

    port = 33122
    dest = "localhost"
    filename = None
    debug = False
    sackMode = False

    for o,a in opts:
        if o in ("-f", "--file="):
            filename = a
        elif o in ("-p", "--port="):
            port = int(a)
        elif o in ("-a", "--address="):
            dest = a
        elif o in ("-d", "--debug="):
            debug = True
        elif o in ("-k", "--sack="):
            sackMode = True

    s = Sender(dest,port,filename,debug, sackMode)
    try:
        s.start()
    except (KeyboardInterrupt, SystemExit):
        exit()
