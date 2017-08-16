#!/usr/bin/env python3
from position import *
from shareMethod import getBits
__author__ = 'Jakub Pelikan'

class StdDecoder():
    '''
    Class implement NIT (Network Information Table) decoder.
    '''
    def __init__(self,bits):
        self.stdData = {'header':None, 'data':[],'crc_32':None}
        self.stdItem = self.getClearStdItem()
        self.leng ={'total':0,'actual':0}
        pos = Position(1472)
        self.readHeader(bits,pos)
        self.readSDT(bits,pos)


    def getClearStdItem(self):
        '''
        Method return clear STD structure
        :return:
        '''
        return {'service_id':None,'reserved_1':None,'EIT_schedule_flag':None,'EIT_present_following_flag':None,'running_status':None
            ,'free_CA_mode':None,'descriptors_loop_length':None,'DVB_DescriptorTag':None,'stdItemSD':None,'descriptor_length':None
            ,'service_type':None,'service_provider_name_length':None,'service_provider_name':''
            ,'service_name_length':None,'service_name':''}

    def readNext(self, bits):
        '''
        Method initialize reading next STD packet
        :param bits: Packet data in bits format
        :return: None
        '''
        pos = Position(1472)
        self.readSDT(bits,pos)

    def readSDT(self, bits,pos):
        '''
        Method initialize reading next STD packet
        :param bits: Packet data in bits format
        :return: None
        '''
        try:
            if self.leng['actual']+184 > self.leng['total']:
                pos.setMinPos((self.leng['total']-self.leng['actual'])*8)
                pos.setCrc()
            else:
                self.leng['actual']=self.leng['actual']+184
            while True:
                if self.stdItem['service_id'] == None: self.stdItem['service_id'] = getBits(bits,pos,16)
                if self.stdItem['reserved_1'] == None: self.stdItem['reserved_1'] = getBits(bits,pos,6)
                if self.stdItem['EIT_schedule_flag'] == None: self.stdItem['EIT_schedule_flag'] = getBits(bits,pos,1)
                if self.stdItem['EIT_present_following_flag'] == None: self.stdItem['EIT_present_following_flag'] = getBits(bits,pos,1)
                if self.stdItem['running_status'] == None: self.stdItem['running_status'] = getBits(bits,pos,3)
                if self.stdItem['free_CA_mode'] == None: self.stdItem['free_CA_mode'] = getBits(bits,pos,1)
                if self.stdItem['descriptors_loop_length'] == None: self.stdItem['descriptors_loop_length'] = getBits(bits,pos,12)
                if self.stdItem['DVB_DescriptorTag'] == None: self.stdItem['DVB_DescriptorTag'] = getBits(bits,pos,8)
                if self.stdItem['DVB_DescriptorTag'] == 72:
                    self.service_descriptor(bits,pos)
                self.stdData['data'].append(self.stdItem)
                self.stdItem = self.getClearStdItem()
        except CRC:
            if self.stdData['crc_32'] == None: self.stdData['crc_32'] = getBits(bits,pos,32,True)
        except PositionZero:
            return

    def readHeader(self, bits,pos):
        '''
        Method read STD header
        :param bits: Packet data in bits format
        :param pos: Position in packet
        :return: None
        '''
        getBits(bits,pos,8)
        header = {'table_id':None,'section_syntax_indicator':None,'reserved_1':None,'reserved_2':None
            ,'section_length':None,'transport_stream_id':None,'reserved_3':None
            ,'version_number':None,'current_next_indicator':None,'section_number':None,'last_section_number':None
            ,'original_network_id':None,'reserved_4':None}
        header['table_id'] = getBits(bits,pos,8)
        header['section_syntax_indicator'] = getBits(bits,pos,1)
        header['reserved_1'] = getBits(bits,pos,1)
        header['reserved_2'] = getBits(bits,pos,2)
        header['section_length'] = getBits(bits,pos,12)
        self.leng['total'] = header['section_length']
        header['transport_stream_id'] = getBits(bits,pos,16)
        header['reserved_3'] = getBits(bits,pos,2)
        header['version_number'] = getBits(bits,pos,5)
        header['current_next_indicator'] = getBits(bits,pos,1)
        header['section_number'] = getBits(bits,pos,8)
        header['last_section_number'] = getBits(bits,pos,8)
        header['original_network_id'] = getBits(bits,pos,16)
        header['reserved_4'] = getBits(bits,pos,8)
        return header

    def service_descriptor(self, bits, pos):
        '''
        Method read service descriptor
        :param bits: Packet data in bits format
        :param pos: Position in packet
        :return: None
        '''
        if self.stdItem['descriptor_length'] == None: self.stdItem['descriptor_length'] = getBits(bits,pos,8)
        if self.stdItem['service_type'] == None: self.stdItem['service_type'] = getBits(bits,pos,8)
        if self.stdItem['service_provider_name_length'] == None: self.stdItem['service_provider_name_length'] = getBits(bits,pos,8)
        if len(self.stdItem['service_provider_name']) != self.stdItem['service_provider_name_length']:
            for x in range(self.stdItem['service_provider_name_length']-len(self.stdItem['service_provider_name'])):
                data = getBits(bits,pos,8)
                self.stdItem['service_provider_name'] = self.stdItem['service_provider_name']+chr(data)
        if self.stdItem['service_name_length'] == None: self.stdItem['service_name_length'] = getBits(bits,pos,8)
        if len(self.stdItem['service_name']) != self.stdItem['service_name_length']:
            for x in range(self.stdItem['service_name_length']-len(self.stdItem['service_name'])):
                data = getBits(bits,pos,8)
                self.stdItem['service_name'] = self.stdItem['service_name']+chr(data)

    def getData(self):
        '''
         Method return STD table data
        :return: STD data
        '''
        return self.stdData

    def isValid(self):
        '''
         Method return if is STD packet valid
        :return: If is valid
        '''
        return (self.stdData['crc_32'] != None)