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
        window_size = 1
        window = []
        block_size = 1400
        f = open(filename, "rb")

        syn = "syn|"+str(sequence_num)+"||"
        sequence_num += 1
        syn += Checksum.generate_checksum(syn)
        if self.debug:
            print ">>>", syn
        self.send(syn)
        res = self.receive()
        if self.debug:
            print "<<<", res

        while True: 
            data = f.read(block_size)
            if not data:
                break
            data_packet = "dat|"+str(sequence_num)+"|"+(data.lstrip()).rstrip()+"|"
            sequence_num += 1
            sequence_num = sequence_num % sequence_num_size
            data_packet += Checksum.generate_checksum(data_packet)
            if self.debug:
                print ">>>", data
            self.send(data_packet)
            res = self.receive()
            if self.debug:
                print "<<<", res

        f.close()

        fin = "fin|"+str(sequence_num)+"||"
        sequence_num += 1
        fin += Checksum.generate_checksum(fin)
        if self.debug:
            print ">>>", fin
        self.send(fin)
        res = self.receive()
        if self.debug:
            print "<<<", res
        sys.exit()


        
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
    debug = True
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
