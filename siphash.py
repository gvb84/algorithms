#!/usr/bin/env python3
"""
SipHash implementation.

Written from scratch based on the original SipHash paper as a lot of
implementations out there seem to be invalid or they deviate slightly.

Not written for performance as it's a pure Python implementation that gets the
job done.

"THE BEER-WARE LICENSE" (Revision 42):
Vincent Berg <gvb@santarago.org> wrote this file.  As long as you retain this
notice you can do whatever you want with this stuff. If we meet some day, and
you think this stuff is worth it, you can buy me a beer in retur
"""


import struct


def Rotl(v, r):
    return (((v << r)) | (v >> (64 - r))) & 0xffffffffffffffff


def SipHalfRound(a, b, c, d, s, t):
    a = (a + b) & 0xffffffffffffffff
    c = (c + d) & 0xffffffffffffffff
    b = Rotl(b, s) ^ a
    d = Rotl(d, t) ^ c
    a = Rotl(a, 32)
    return (a, b, c, d)


def SipRound(v0, v1, v2, v3):
    v0, v1, v2, v3 = SipHalfRound(v0, v1, v2, v3, 13, 16)
    v2, v1, v0, v3 = SipHalfRound(v2, v1, v0, v3, 17, 21)
    return (v0, v1, v2, v3)


class SipHash:
    def __init__(self, c=2, d=4):
        self.c = 2
        self.d = 4

    def __call__(self, m, k):
        assert len(k) == 16

        # initialization
        k0, k1 = struct.unpack("<QQ", k)
        v0 = k0 ^ 0x736f6d6570736575
        v1 = k1 ^ 0x646f72616e646f6d
        v2 = k0 ^ 0x6c7967656e657261
        v3 = k1 ^ 0x7465646279746573

        # compression
        b = len(m)
        w = (b + 1) // 8
        for i in range(w-1):
            mi, = struct.unpack("<Q", m[i:i+8])
            v3 ^= mi
            for j in range(self.c):
                v0, v1, v2, v3 = SipRound(v0, v1, v2, v3)
            v0 ^= mi

        mi = b << 56  # encode length in LSB
        w <<= 3  # offset in 64-bit values
        for i in range(0, (b % 8)):
            mi |= (m[b-(b % 8)+i] << (i << 3))
        v3 ^= mi
        for j in range(self.c):
            v0, v1, v2, v3 = SipRound(v0, v1, v2, v3)
        v0 ^= mi

        # finalization
        v2 ^= 0xff
        for i in range(self.d):
            v0, v1, v2, v3 = SipRound(v0, v1, v2, v3)

        return ((v0 ^ v1 ^ v2 ^ v3) & 0xffffffffffffffff)


if __name__ == "__main__":
    # test with vectors from the SipHash paper
    test_vector = bytearray(15)
    test_key = bytearray(16)
    for i in range(15):
        test_vector[i] = i
        test_key[i] = i
    test_key[15] = 0x0f
    h = SipHash(2, 4)
    res = h(test_vector, test_key)
    assert(res == 0xa129ca6149be45e5)
