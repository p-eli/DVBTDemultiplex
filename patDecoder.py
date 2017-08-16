#!/usr/bin/env python3

from shareMethod import getBits
from position import *
__author__ = 'Jakub Pelikan'


class PatDecoder():
    '''
    Class implement PAT decoder.
    Return list of all programs available in the transport stream.
    '''
    def __init__(self, bits):
        self.leng ={'total':0,'actual':0}
        self.patData = {'header':None, 'data':[],'crc_32':None}
        self.patItem = self.getClearPatItem()
        pos = Position(1472)
        self.patData['header'] = self.readHeader(bits,pos)
        self.readPAT(bits,pos)

    def getClearPatItem(self):
        '''
        Method return clear PAT structure
        :return:
        '''
        return {'program_number':None, 'reserved':None, 'network_PID':None,'program_map_pid':None}

    def readNext(self,bits):
        '''
        Method initialize reading next PAT packet
        :param bits: Packet data in bits format
        :return: None
        '''
        pos = Position(1472)
        self.readPAT(bytes,pos)

    def readPAT(self, bits,pos):
        '''
        Method decode next PAT packet
        :param bits: Packet data in bits format
        :param pos: Position in packet
        :return: None
        '''
        try:
            if self.leng['actual']+184 > self.leng['total']:
                pos.setMinPos((self.leng['total']-self.leng['actual'])*8)
                pos.setCrc()
            else:
                self.leng['actual']=self.leng['actual']+184

            while True:
                if self.patItem['program_number'] == None: self.patItem['program_number'] = getBits(bits,pos,16)
                if self.patItem['reserved'] == None: self.patItem['reserved'] = getBits(bits,pos,3)
                if self.patItem['program_number'] == 0:
                    if self.patItem['network_PID'] == None: self.patItem['network_PID'] = getBits(bits,pos,13)
                else:
                    if self.patItem['program_map_pid'] == None: self.patItem['program_map_pid'] = getBits(bits,pos,13)
                self.patData['data'].append(self.patItem)
                self.patItem = self.getClearPatItem()
        except CRC:
            if self.patData['crc_32']  == None: self.patData['crc_32'] = getBits(bits,pos,32,True)
        except PositionZero:
            return()

    def readHeader(self,bits,pos):
        '''
        Method read header of nit packet
        :param bits: Packet data in bits format
        :param pos: Position in packet
        :return: None
        '''
        getBits(bits,pos,8)
        header = {'table_id':None,'section_syntax_indicator':None,'fixed':None,'reserved_1':None,'section_length':None
                     ,'transport_stream_id':None,'reserved_2':None,'version_number':None,'current_next_indicator':None
                     ,'section_number':None,'last_section_number':None}
        header['table_id'] = getBits(bits,pos,8)
        header['section_syntax_indicator'] = getBits(bits,pos,1)
        header['fixed'] = getBits(bits,pos,1)
        header['reserved_1'] = getBits(bits,pos,2)
        header['section_length'] = getBits(bits,pos,12)
        self.leng['total'] = header['section_length']
        header['transport_stream_id'] = getBits(bits,pos,16)
        header['reserved_2'] = getBits(bits,pos,2)
        header['version_number'] = getBits(bits,pos,5)
        header['current_next_indicator'] = getBits(bits,pos,1)
        header['section_number'] = getBits(bits,pos,8)
        header['last_section_number'] = getBits(bits,pos,8)
        return header

    def isValid(self):
        '''
         Method return if is PAT packet valid
        :return: If is valid
        '''
        return(self.patData['crc_32'] != None)

    def getData(self):
        '''
         Method return PAT table data
        :return: Pat data
        '''
        return self.patData