#!/usr/bin/env python3

from shareMethod import getBits
from position import *
__author__ = 'Jakub Pelikan'

class PmtDecoder():
    '''
    Class implement PMT decoder.
    List of all programs available in the transport stream
    '''
    def __init__(self, bits):
        self.leng ={'total':0,'actual':0}
        self.pmtData = {'header':None,'data':[],'crc_32':None}
        self.pmtItem = self.getClearPmtItem()
        self.pmtStreamItem = self.getClearPmtItem()
        self.CRC_32 = None
        pos = Position(1472)
        self.pmtData['header']=self.readHeader(bits,pos)
        self.readPMT(bits,pos)

    def getClearPmtItem(self):
        '''
        Method return clear PMT structure
        :return:
        '''
        return {'stream_type':None,'reserved_1':None,'elementary_PID':None,'reserved_2':None,'ES_info_length':None,'MPEG_DescriptorTag':None, 'descriptor_length':None,'multiple_frame_rate_flag':None,'frame_rate_code':None
            ,'MPEG_1_only_flag':None,'constrained_parameter_flag':None,'still_picture_flag':None,'ISO639_language_code':'','Audio_type':None,'DVB_DescriptorTag':None}


    def readNext(self,bits,pos):
        '''
        Method initialize reading next PMT packet
        :param bits: Packet data in bits format
        :return: None
        '''
        pos = Position(1472)
        self.readPMT(bits,pos)

    def readPMT(self, bits,pos):
        '''
        Method decode next PMT packet
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
                if self.pmtItem['stream_type'] == None: self.pmtItem['stream_type'] = getBits(bits,pos,4)
                if self.pmtItem['reserved_1'] == None: self.pmtItem['reserved_1'] = getBits(bits,pos,4)
                if self.pmtItem['elementary_PID'] == None: self.pmtItem['elementary_PID'] = getBits(bits,pos,12)
                if self.pmtItem['reserved_2'] == None: self.pmtItem['reserved_2'] = getBits(bits,pos,4)
                if self.pmtItem['ES_info_length'] == None: self.pmtItem['ES_info_length'] = getBits(bits,pos,12)
                getBits(bits,pos,self.pmtItem['ES_info_length']*8)
                getBits(bits,pos,4)
                self.pmtData['data'].append(self.pmtItem)
                self.pmtItem = self.getClearPmtItem()
        except CRC:
            if self.pmtData['crc_32']  == None: self.pmtData['crc_32'] = getBits(bits,pos,32,True)
        except PositionZero:
            return

    def streamType2(self, bits, pos):
        '''
        Method decode stream type 2
        :param bits: Packet data in bits format
        :param pos: Position in packet
        :return: None
        '''
        if self.pmtItem['MPEG_DescriptorTag'] == None: self.pmtItem['MPEG_DescriptorTag'] = getBits(bits,pos,8)
        if self.pmtItem['descriptor_length'] == None: self.pmtItem['descriptor_length'] = getBits(bits,pos,8)
        if self.pmtItem['multiple_frame_rate_flag'] == None: self.pmtItem['multiple_frame_rate_flag'] = getBits(bits,pos,1)
        if self.pmtItem['frame_rate_code'] == None: self.pmtItem['frame_rate_code'] = getBits(bits,pos,4)
        if self.pmtItem['MPEG_1_only_flag'] == None: self.pmtItem['MPEG_1_only_flag'] = getBits(bits,pos,1)
        if self.pmtItem['constrained_parameter_flag'] == None: self.pmtItem['constrained_parameter_flag'] = getBits(bits,pos,1)
        if self.pmtItem['still_picture_flag'] == None: self.pmtItem['still_picture_flag'] = getBits(bits,pos,1)

    def streamType3(self, bits, pos):
        '''
        Method decode stream type 3
        :param bits: Packet data in bits format
        :param pos: Position in packet
        :return: None
        '''
        if self.pmtItem['MPEG_DescriptorTag'] == None: self.pmtItem['MPEG_DescriptorTag'] = getBits(bits,pos,8)
        if self.pmtItem['descriptor_length'] == None: self.pmtItem['descriptor_length'] = getBits(bits,pos,8)
        if self.pmtItem['descriptor_length'] > 0:
            pos.addMin(self.pmtItem['descriptor_length']*8)
            try:
                while True:
                    if self.pmtItem['ISO639_language_code'] == None: self.pmtItem['ISO639_language_code'] = self.pmtItem['ISO639_language_code']+getBits(bits,pos,8)
            except MinimalPosition:
                pass
            if self.pmtItem['Audio_type'] == None: self.pmtItem['Audio_type'] = getBits(bits,pos,8)

    def readHeader(self,bits,pos):
        '''
        Method read PMT header
        :param bits: Packet data in bits format
        :param pos: Position in packet
        :return: None
        '''
        header = {'table_id':None,'section_syntax_indicator':None,'fixed':None,'reserved_1':None,'section_length':None
                     ,'program_number':None,'reserved_2':None,'version_number':None,'current_next_indicator':None
                     ,'section_number':None,'last_section_number':None,'reserved_3':None,'PCR_PID':None,'reserved_4':None
                     ,'program_info_length':None}
        getBits(bits,pos,8)
        header['table_id'] = getBits(bits,pos,8)
        header['section_syntax_indicator'] = getBits(bits,pos,1)
        header['fixed'] = getBits(bits,pos,1)
        header['reserved_1'] = getBits(bits,pos,2)
        header['section_length'] = getBits(bits,pos,12)
        self.leng['total'] = header['section_length']
        header['program_number'] = getBits(bits,pos,16)
        header['reserved_2'] = getBits(bits,pos,2)
        header['version_number'] = getBits(bits,pos,5)
        header['current_next_indicator'] = getBits(bits,pos,1)
        header['section_number'] = getBits(bits,pos,8)
        header['last_section_number'] = getBits(bits,pos,8)
        header['reserved_3'] = getBits(bits,pos,4)
        header['PCR_PID'] = getBits(bits,pos,12)
        header['reserved_4'] = getBits(bits,pos,4)
        header['program_info_length'] = getBits(bits,pos,16)
        return header

    def isValid(self):
        '''
         Method return if is PMT packet valid
        :return: If is valid
        '''
        return(self.pmtData['data'] != None)

    def getData(self):
        '''
         Method return PMT table data
        :return: PMT data
        '''
        return self.pmtData

    def getAudioChanel(self):
        '''
        Method return audio chanel PID
        :return: audio chanel PID
        '''
        for item in self.pmtData['data']:
            if item['stream_type'] == 3:
                return item['elementary_PID']

    def getVideoChanel(self):
        '''
        Method return video chanel PID
        :return: video chanel PID
        '''
        for item in self.pmtData['data']:
            if item['stream_type'] == 2:
                return item['elementary_PID']

    def getOtherChanel(self):
        '''
        Method return no video/audio chanel's PID
        :return: chanel PID
        '''
        result = []
        for item in self.pmtData['data']:
            result.append(item['elementary_PID'])
        result.remove(self.getAudioChanel())
        result.remove(self.getVideoChanel())
        return result

    def getAllChanel(self):
        '''
        Method return list of all chanel
        :return: chanel's PID
        '''
        result = []
        for item in self.pmtData['data']:
            result.append(item['elementary_PID'])
        return result