#!/usr/bin/env python3
from position import*
from shareMethod import getBits
__author__ = 'Jakub Pelikan'

class NitDecoder():
    '''
    Class implement NIT (Network Information Table) decoder.
    '''
    def __init__(self,bits):
        pos = Position(1472 - 8)
        pos.setCrc()
        self.nitData = self.getClearNitData()
        self.readNIT(bits,pos)

    def readNIT(self,bits,pos):
        '''
        Method read nit packet
        :param bits: Packet data in bits format
        :param pos: Position in packet
        :return:
        '''
        try:
            self.nitData['table_id'] = getBits(bits,pos,8)
            self.nitData['section_syntax_indicator'] = getBits(bits,pos,1)
            self.nitData['reserved_1'] = getBits(bits,pos,1)
            self.nitData['reserved_2'] = getBits(bits,pos,2)
            self.nitData['section_length'] = getBits(bits,pos,12)
            pos.setMinPos(self.nitData['section_length']*8)
            self.nitData['network_id'] = getBits(bits,pos,16)
            self.nitData['reserved_3'] = getBits(bits,pos,2)
            self.nitData['version_number'] = getBits(bits,pos,5)
            self.nitData['current_next_indicator'] = getBits(bits,pos,1)
            self.nitData['section_number'] = getBits(bits,pos,8)
            self.nitData['last_section_number'] = getBits(bits,pos,8)
            self.nitData['reserved_4'] = getBits(bits,pos,4)
            self.nitData['network_descriptors_length'] = getBits(bits,pos,12)
            pos.addMin(self.nitData['network_descriptors_length']*8)
            try:
                while True:
                    self.nitData['DVBDescriptorTags'].append(self.DVBDescriptorTagDecoder(bits, pos))
            except MinimalPosition:
                pass
            self.nitData['reserved_5'] = getBits(bits,pos,4)
            self.nitData['transport_stream_loop_length'] = getBits(bits,pos,12)
            pos.addMin(self.nitData['transport_stream_loop_length']*8)
            try:
                while True:
                    item = {'transport_stream_ID':None,'original_network_ID':None,'reserved':None
                        ,'transport_descriptors_length':None,'DVBDescriptorTags':[]}
                    item['transport_stream_ID'] = getBits(bits,pos,16)
                    self.nitData['transport_stream_loop'].append(item)
                    item['original_network_ID'] = getBits(bits,pos,16)
                    item['reserved'] = getBits(bits,pos,4)
                    item['transport_descriptors_length'] = getBits(bits,pos,12)
                    pos.addMin(item['transport_descriptors_length']*8)
                    try:
                        while True:
                            item['DVBDescriptorTags'].append(self.DVBDescriptorTagDecoder(bits, pos))
                    except MinimalPosition:
                        pass
            except MinimalPosition:
                pass
        except CRC:
            self.nitData['CRC_32'] = getBits(bits,pos,32,True)

    def DVBDescriptorTagDecoder(self,bits,pos):
        '''
        DVB deskriptor tag Decoder
        :param bits: Data in bits format
        :param pos: position in packet
        :return:
        '''
        item = {'DVB_descriptor_tag':None,'descriptor_length':None,'data':None}
        item['DVB_descriptor_tag'] = getBits(bits,pos,8)
        item['descriptor_length'] =getBits(bits,pos,8)
        if item['DVB_descriptor_tag'] == 74: #linkage deskroptor
            item['data'] = self.linkageDescriptor(bits,pos)
        elif item['DVB_descriptor_tag'] == 90: #terrestrial_delivery_system_descriptor
            item['data'] = self.terrestrialDeliverySystemDescriptor(bits,pos)
        elif item['DVB_descriptor_tag'] == 98: #frequency_list_descriptor
            pos.addMin(item['descriptor_length']*8)
            item['data'] = self.frequencyListDescriptor(bits,pos)
        elif item['DVB_descriptor_tag'] == 64:
            pos.addMin(item['descriptor_length']*8)
            item['data'] = self.networkNameDescriptor(bits, pos)
        else:
            return None
        return item

    def networkNameDescriptor(self, bits, pos):
        '''
        Method read network name descriptor
        :param bits: Data in bits format
        :param pos: position in packet
        :return: string with Network name descriptor
        '''
        Network_name = ''
        try:
            while True:
                data = getBits(bits,pos,8)
                Network_name = Network_name+chr(data)
        except MinimalPosition:
            return Network_name

    def linkageDescriptor(self, bits, pos):
        '''
        Method decode linkage descriptor
        :param bits: Data in bits format
        :param pos: position in packet
        :return:
        '''
        item = {'transport_stream_ID':None,'original_network_ID':None,'service_ID':None,'linkage_type':None
            ,'OUI_data_length':None,'OUI':None,'selector_length':None}
        item['transport_stream_ID'] = getBits(bits,pos,16)
        item['original_network_ID'] = getBits(bits,pos,16)
        item['service_ID'] = getBits(bits,pos,16)
        item['linkage_type'] = getBits(bits,pos,8)
        item['OUI_data_length'] = getBits(bits,pos,8)
        item['OUI'] = getBits(bits,pos,24)
        item['selector_length'] = getBits(bits,pos,8)
        return item

    def terrestrialDeliverySystemDescriptor(self, bits, pos):
        '''
         Method decode terrestrial delivery system descriptor
        :param bits: Data in bits format
        :param pos: position in packet
        :return:
        '''
        item = {'center_frequency':None,'brandwidth':None,'brandwidthValue':None,'priority':None,'time_slicing_indicator':None,'MPE_FEC_indicator':None
            ,'reserved_1':None,'constellation':None,'constellationValue':None,'hierarchy_information':None,'Code_rate_HP_stream':None,'Code_rate_LP_stream':None, 'code_rateValue':None
            ,'guard_interval':None,'guard_intervalValue':None,'transmission_mode':None,'other_frequency_flag':None,'reserved_future_use':None}

        item['center_frequency'] = getBits(bits,pos,32)
        item['brandwidth'] = getBits(bits,pos,3)
        item['brandwidthValue'] = self.getBrandwitchValue(item['brandwidth'])
        item['priority'] = getBits(bits,pos,1)
        item['time_slicing_indicator'] = getBits(bits,pos,1)
        item['MPE_FEC_indicator'] = getBits(bits,pos,1)
        item['reserved_1'] = getBits(bits,pos,2)
        item['constellation'] = getBits(bits,pos,2)
        item['constellationValue'] = self.getConstellationValue(item['constellation'])
        item['hierarchy_information'] = getBits(bits,pos,3)
        item['Code_rate_HP_stream'] = getBits(bits,pos,3)
        item['code_rateValue'] = self.getCodeRateValue(item['Code_rate_HP_stream'])
        item['Code_rate_LP_stream'] = getBits(bits,pos,3)
        item['guard_interval'] = getBits(bits,pos,2)
        item['guard_intervalValue']=self.getGuardIntervalValue(item['guard_interval'])
        item['transmission_mode'] = getBits(bits,pos,2)
        item['other_frequency_flag'] = getBits(bits,pos,1)
        item['reserved_future_use'] = getBits(bits,pos,32)
        return item

    def frequencyListDescriptor(self,bits,pos):
        '''
         Method decode frequency list descriptor
        :param bits: Data in bits format
        :param pos: position in packet
        :return:
        '''
        item = {'reserved_future_use':None,'coding_type':None, 'centre_frequency':[]}
        item['reserved_future_use'] = getBits(bits,pos,6)
        item['coding_type'] = getBits(bits,pos,2)
        try:
            while True:
                item['centre_frequency'].append(getBits(bits,pos,32))
        except:
            return item

    def getClearNitData(self):
        '''
         Method return clear nit data structure
        :return: clear Nit data structure
        '''
        return {'table_id':None,'section_syntax_indicator':None,'reserved_future_use':None,'reserved_1':None,'reserved_2':None
            ,'section_length':None,'network_id':None,'reserved_3':None,'version_number':None,'current_next_indicator':None,'section_number':None
            ,'last_section_number':None,'reserved_4':None,'network_descriptors_length':None,'DVBDescriptorTags':[],'reserved_5':None
            ,'transport_stream_loop_length':None,'transport_stream_loop':[],'CRC_32':None}

    def isValid(self):
        '''
         Method return if is NIT packet valid
        :return: If is valid
        '''
        return (self.nitData['CRC_32'] != None)

    def getData(self):
        '''
         Method return nit table data
        :return: Nit data
        '''
        return self.nitData

    def getBrandwitchValue(self, val):
        '''
         Method decode brandwitch value
        :param val: decoded value
        :return: String with brandwitch value
        '''
        if val == 0:
            return '8 MHz'
        elif val == 1:
            return '7 MHz'
        elif val == 2:
            return '6 MHz'
        elif val == 3:
            return '5 MHz'
        else:
            return 'Reserved for future use'

    def getConstellationValue(self,val):
        '''
         Method decode constellation value
        :param val: decoded value
        :return: String with constellation value
        '''
        if val == 0:
            return 'QPSK'
        elif val == 1:
            return '16-QAM'
        elif val == 2:
            return '64-QAM'
        else:
            return 'Reserved for future use'

    def getGuardIntervalValue(self,val):
        '''
         Method decode guard interval value
        :param val: decoded value
        :return: String with guard interval value
        '''
        if val == 0:
            return '1/32'
        elif val == 1:
            return '1/16'
        elif val == 2:
            return '1/8'
        elif val == 3:
            return '1/4'

    def getCodeRateValue(self,val):
        '''
         Method decode code rate value
        :param val: decoded value
        :return: String with code rate value
        '''
        if val == 0:
            return '1/2'
        elif val == 1:
            return '2/3'
        elif val == 2:
            return '3/4'
        elif val == 3:
            return '5/6'
        elif val == 4:
            return '7/8'
        else:
            return 'reserved for future use'

    def getBitrate(self):
        '''
        Method compute stream bitrate
        :return: stream bitrate
        '''
        data = {'networkName':0,'network_id':0,'brandwidth':0,'constellation':0,'guard_interval':0,'code_rate':0}
        for x in self.nitData['transport_stream_loop']:
            for y in x['DVBDescriptorTags']:
                if y['DVB_descriptor_tag'] == 90:
                    data['brandwidth'] = (y['data']['brandwidth'])+1
                    val = y['data']['constellation']
                    if val == 0:
                        data['constellation'] = 1/4
                    elif val == 1:
                        data['constellation'] = 1/2
                    elif val == 2:
                        data['constellation'] = 3/4
                        val = y['data']['Code_rate_HP_stream']
                    if val == 0:
                        data['code_rate'] = 1/2
                    elif val == 1:
                        data['code_rate'] = 2/3
                    elif val == 2:
                        data['code_rate'] = 3/4
                    elif val == 3:
                        data['code_rate'] = 5/6
                    elif val == 4:
                        data['code_rate'] = 7/8
                    val = y['data']['guard_interval']
                    if val == 0:
                        data['guard_interval'] = 32/33
                    elif val == 1:
                        data['guard_interval'] = 16/17
                    elif val == 2:
                        data['guard_interval'] = 8/9
                    elif val == 3:
                        data['guard_interval'] = 4/5
                    break
        return ( 54000000*(188/204) * (data['brandwidth']))*(data['constellation']) * (data['code_rate']) * (data['guard_interval'])