#!/usr/bin/env python3
__author__ = 'Jakub Pelikan'


class Position():
    '''
    Class implement position pointer for work with bits packet data
    '''
    def __init__(self, value):
        self.pos = value
        self.min = 0
        self.crc = False
        self.subMin = [0]

    def dec(self, int, crc=False):
        '''
        Method decrement position in packet
        :param int: Decrement number
        :param crc: if decrement for reading crc bits
        :return: None
        '''
        self.pos = self.pos - int
        if self.pos < 0:
            raise PositionZero()
        if (not crc) and self.crc and (self.pos < self.min):
            self.pos = self.pos+int
            raise CRC()
        if crc and self.crc :
            return
        if not crc and (self.pos < self.min) :
            self.pos = self.pos + int
            raise DataEnd()
        if self.pos < self.subMin[-1] and self.subMin[-1]!=0:
            self.pos = self.pos + int
            self.subMin.remove(self.subMin[-1])
            raise MinimalPosition()

    def setMinPos(self, min):
        '''
        Method set minimal position
        :param min: Minimal position
        :return:
        '''
        self.min = 1472-(min)

    def setCrc(self):
        '''
        Method set crc in packet
        :return:
        '''
        self.crc = True

    def addMin(self,min):
        '''
        Method add minimal temporary position
        :param min:
        :return:
        '''
        self.subMin.append(self.pos - (min))


class DataEnd(Exception):
    '''
    Data End Exception
    '''
    pass


class CRC(Exception):
    '''
    CRC exception
    '''
    pass


class PositionZero(Exception):
    '''
    Position Zero exception
    '''
    pass


class MinimalPosition(Exception):
    '''
    Minimal position exception
    '''
    pass