#!/usr/bin/env python
#      Polygraph (release 0.1)
#      Signature generation algorithms for polymorphic worms
#
#      Copyright (c) 2004-2005, Intel Corporation
#      All Rights Reserved
#
#  This software is distributed under the terms of the Eclipse Public
#  License, Version 1.0 which can be found in the file named LICENSE.
#  ANY USE, REPRODUCTION OR DISTRIBUTION OF THIS SOFTWARE CONSTITUTES
#  RECIPIENT'S ACCEPTANCE OF THIS AGREEMENT

from __future__ import division
import sys
import string

class Context:
    def __init__(self):
        self.count = 0
        self.bytes = {}

    def increment(self, byte):
        self.count += 1
        if self.bytes.has_key(byte):
            self.bytes[byte] += 1
        else:
            self.bytes[byte] = 1

class PortInfo:
    def __init__(self, port, windowsize):
        self.contexts = {}
        self.byte_count = 0
        self.con_count = 0
        self.pkt_count = 0
        self.port = port
        self.windowsize = windowsize

    def process_connection(self, con):
        self.con_count += 1
        self.pkt_count += con["pkts"]

        # process stream
        for i in xrange(len(con["data"])):
            for context_len in xrange(self.windowsize):
                if context_len > i: break
                context = con["data"][i-context_len:i]
                byte = con["data"][i]
                if not self.contexts.has_key(context):
#                    self.contexts[context] = Context()
                    self.contexts[context] = {'count': 0, 'bytes': {}}
#                self.contexts[context].increment(con["data"][i])
                if not self.contexts[context]['bytes'].has_key(byte):
                    self.contexts[context]['bytes'][byte] = 0
                self.contexts[context]['bytes'][byte] += 1
                self.contexts[context]['count'] += 1

    def write_results(self):
        import pickle
        outfile = open ("port." + str(self.port) + ".pickle", 'w')
        pickle.dump(self.contexts, outfile, True)
        outfile.close()

        outfile = open ("port." + str(self.port), 'w')
#        outfile.write("# count\tfraction\tsequence\n")

        # sorted from highest count to lowest
        results = self.contexts.items()
        results.sort(lambda x, y: cmp(y[1]['count'], x[1]['count']))

        for (bytes, context) in results:
            outfile.write("# context %s found %d times\n" % (bytes.__repr__(), context['count']))
            byte_counts = context['bytes'].items()
            byte_counts.sort(lambda x, y: cmp(y[1], x[1]))
            for (byte, count) in byte_counts:
                outfile.write("\t%s\t%d\n" % (byte.__repr__(), count))
#            outfile.write("%u\t%f\t%s\n" % (
#                            cnt, cnt / self.con_count, seq.__repr__()))

#        outfile.write("# %d of %d (%f%%) sequences never found\n" % (
#            2**(8*window_size) - len(self.seq_counts),
#            2**(8*window_size),
#            (1 - len(self.seq_counts)/(2**(8*window_size))) * 100))
        outfile.write("# %d connections\t%d pkts\n" % (
                        self.con_count, self.pkt_count))
        outfile.close()

class Counters:
    def __init__(self, windowsize):
        self.ctrs = {}
        self.windowsize = windowsize

    def process_connection(self, con):
        port = con["connection"][3]
        if not self.ctrs.has_key(port):
            self.ctrs[con["connection"][3]] = PortInfo(port, windowsize)
        self.ctrs[port].process_connection(con)

    def write_results(self):
        sorted_keys = self.ctrs.keys()
        sorted_keys.sort()
        for port in sorted_keys:
            self.ctrs[port].write_results()

    def monitoring_port(self, port):
        return self.ctrs.has_key(port)

if __name__ == "__main__":
    import stream_trace
    windowsize = int(sys.argv[1])
    counters = Counters(windowsize)
    st = stream_trace.StreamTrace(sys.argv[2])

    try:
        sample = st.next()
        while sample:
            con = {'connection': [0]*4, 'pkts':1, 'data':sample}
            counters.process_connection(con)
            sample = st.next()
    except KeyboardInterrupt:
        print "Interrupted! Writing partial results"
    counters.write_results()
    sys.exit()



    import pkts_to_streams
    # seq size to consider (in bytes)
    windowsize = int(sys.argv[1])
    # time before considering a connection completed
    timeout = 200

    counters = Counters(windowsize)
    filter = ("dst port 80")     # http
#          "dst port 443 or "    # https 
#          "dst port 25 or "     # smtp
#          "dst port 53 or "     # dns
#          "dst port 23 or "     # telnet 
#          "dst port 2401 or "   # cvs pserver 
#          "dst port 20 or "     # ftp-data
#          "dst port 21"         # ftp
#          ) 

# use psyco if it's there to speed things up
#try:
#    import psyco
#    psyco.full()
#except ImportError:
#    pass

    try:
        for dump_file in sys.argv[2:]:
            print "Processing %s..." % dump_file
            pkts_to_streams.process_trace(dump_file, counters.process_connection, 
                                            timeout, filter)
    except KeyboardInterrupt: 
        print "Interrupted! Writing partial results..."

    counters.write_results()
