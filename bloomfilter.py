#!/usr/bin/env python3
"""
Counting BloomFilter implementation.

Written from scratch. Not written for performance as it's a pure Python
implementation that gets the job done for me now. Please note that it will
throw Exceptions the moment a certain bucket goes over the maximum value that
can be stored in a byte (>255). If it's necessary and/or very likely that data
needs to be stored with higher counts then this implementation should be
adjusted or another implementation should be found.

If the counts get so high because of many bucket collisions then one should
simply increase the capacity and decrease the error_rate properties when
constructing the filter to make these events very unlikely.

The hash function used is SipHash-2-4 but this can easily be changed.

"THE BEER-WARE LICENSE" (Revision 42):
Vincent Berg <gvb@santarago.org> wrote this file.  As long as you retain this
notice you can do whatever you want with this stuff. If we meet some day, and
you think this stuff is worth it, you can buy me a beer in retur
"""

from math import log, ceil

from siphash import SipHash


class CountingBloomFilter(set):
    def __init__(self, capacity, error_rate, max_count=255):
        assert(capacity > 0)
        assert(max_count > 0 and max_count < 256)
        assert(error_rate > 0 and error_rate < 1)

        self.n = n = capacity
        self.p = p = error_rate

        # calculate number of hash functions k based on
        # k = -(ln(p)/ln(2)) = -log_2 p
        self.k = ceil(abs(log(p) / log(2)))

        # length of bloom filter in bits
        # m = -((n*ln(p))/(ln(2)^2))
        self.m = ceil(abs(n*log(p))/pow(log(2), 2))

        # offset within array to use per hash function
        self.o = ceil(self.m/self.k)

        # current amount of entries
        self.c = 0

        self.count_array = bytearray(self.m)
        self.hasher = SipHash()
        self.hash_key = bytearray(16)

    def __len__(self):
        return self.c

    def __contains__(self, item):
        for i, h in enumerate(self.hash(item)):
            off = h + (i * self.o)
            if self.count_array[off] == 0:
                return False
        return True

    def __repr__(self):
        return "BloomFilter <k:%i, m:%i, n:%i, p:%.8f>" % \
               (self.k, self.m, self.n, self.p)

    def hash(self, data):
        h = self.hasher(data, self.hash_key)
        h1, h2 = ((h >> 32) & 0xffffffff), (h & 0xffffffff)
        ret = []
        for i in range(self.k):
            h_i = (h1 + i * h2) % self.o
            ret.append(h_i)
        return ret

    def additem(self, item):
        for i, h in enumerate(self.hash(item)):
            off = h + (i * self.o)
            self.count_array[off] += 1
        self.c += 1

    def delitem(self, item):
        for i, h in enumerate(self.hash(item)):
            off = h + (i * self.o)
            self.count_array[off] -= 1
        self.c -= 1


if __name__ == "__main__":
    bf = CountingBloomFilter(100000, .0001)
    data = [b"A", b"", b"helloworld"]
    import random
    for i in range(0, 50):
        data.append(bytearray([random.randint(0, 255) for _ in range(100)]))
    assert(bf.c == 0)
    for k in data:
        assert(k not in bf)
        bf.additem(k)
        assert(k in bf)
    assert(bf.c == len(data))
    for k in data:
        bf.delitem(k)
        assert(k not in bf)
    assert(bf.c == 0)
