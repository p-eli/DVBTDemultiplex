#!/usr/bin/env python3
__author__ = 'Jakub Pelikan'

def getBits(bytes, startBit, bits,crc=False):
    '''
     Method return bits from startBit n bits
    :param startBit Start bit in bits
    :param bits Number of bits
    :crc if reading crc bits
    :return: n bits
    '''
    startBit.dec(bits, crc)
    mask = ((pow(2,(bits))-1))
    return (bytes >> startBit.pos) & mask