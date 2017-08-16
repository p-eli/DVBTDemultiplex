#!/usr/bin/env python3
from nitDecoder import NitDecoder
from patDecoder import PatDecoder
from sdtDecoder import StdDecoder
from pmtDecoder import PmtDecoder
from videoDecoder import VideoDecoder
from audioDecoder import AudioDecoder
from position import Position
from shareMethod import getBits
import re
import os
__author__ = 'Jakub Pelikan'

class DVBTDemultiplex():
    '''
    Class implement demultiplexor of DVBT stream
    '''
    def __init__(self):
        self.sdt = None
        self.nit = None
        self.pat = None
        self.pcr = None
        self.pidDict = {}
        self.structureReady = False
        self.chanel = {}
        self.radioServicePID = {}
        self.servicePID = {}
        self.radioChanel = {}
        self.packetNumber = 0

    def readFile(self, file):
        '''
        Method read ts file a create alone audio and video files
        :param file: path and name to ts file
        :return: None
        '''
        self.inputFile = file
        self.folderName = re.sub('\.ts','',self.inputFile)
        self.openFile()
        self.writePIDToInfoTXT()
        self.writeAudio()

    def openFile(self):
        '''
        Method open,read and process ts file
        :return: None
        '''
        with open(self.inputFile,mode='rb') as file:
            self.createFolder('./',self.folderName)
            while True:
                self.packetNumber = self.packetNumber + 1
                headerByte = file.read(4)
                if not headerByte: break
                header = self.readHeader(int.from_bytes(headerByte, byteorder='big'))
                payloadByte = file.read(184)
                if header['transport_error_indicator'] == 0:
                    if not payloadByte: break
                    if (header['adaptation_field_control'] !=0):
                        self.readAdaptionField(header['pid'],int.from_bytes(payloadByte, byteorder='big'))
                    if (header['payload_flag'] !=0):
                        self.readPayloadData(header['pid'],int.from_bytes(payloadByte, byteorder='big'), header, payloadByte)

    def readHeader(self, bits):
        '''
        Method read header of ts file
        :param bits: header bits
        :return: header structure
        '''
        pos = Position(32)
        sync_byte = getBits(bits,pos,8)
        transport_error_indicator = getBits(bits,pos,1)
        payload_unit_start_indicator = getBits(bits,pos,1)
        transport_priority = getBits(bits,pos,1)
        pid = getBits(bits,pos,13)
        if not pid in self.pidDict.keys():
            self.pidDict[pid] = {'count':0, 'byterate':0}
        else:
            self.pidDict[pid]['count'] = self.pidDict[pid]['count'] + 1
        transport_scrambling_control = getBits(bits,pos,2)
        adaptation_field_control = getBits(bits,pos,1)
        payload_flag = getBits(bits,pos,1)
        continuity_counter = getBits(bits,pos,4)
        return({'sync_byte':sync_byte,'transport_error_indicator':transport_error_indicator
                ,'payload_unit_start_indicator':payload_unit_start_indicator,
                'transport_priority':transport_priority,'pid':pid,
                'transport_scrambling_control':transport_scrambling_control,
                'adaptation_field_control':adaptation_field_control,
                'payload_flag':payload_flag,'continuity_counter':continuity_counter})

    def readPayloadData(self, pid, bytes, header, bits):
        '''
        Method read and process payload data
        :param pid: Packet ID
        :param bytes: data in bytes format
        :param header: header data
        :param bits: data in bits format
        :return:
        '''
        if pid == 0:
            if header['payload_unit_start_indicator'] == 1: #first packet
                if self.pat == None:
                    self.pat = PatDecoder(bytes)
                elif not self.pat.isValid():
                    self.pat = PatDecoder(bytes)
            elif self.pat != None and not self.pat.isValid():
                self.pat.readNext(bytes)
            if not self.structureReady and self.sdt != None and self.pat !=None and self.sdt.isValid() and self.pat.isValid(): self.createFolderStructure()
        elif pid == 1: #CAT - Conditional Access Table
            pass
        elif pid == 2: #Transport Stream Description Table contains descriptors relating to the overall transport stream
            pass
        elif pid == 3: #IPMP Control Information Table contains a directory listing of all ISO/IEC 14496-13 control streams used by Program Map Tables
            pass
        elif (pid >= 4) and (pid <=15): #Reserved for future use
            pass
        elif(pid >=16) and (pid <=31):
            if pid == 16:
                if header['payload_unit_start_indicator'] == 1:
                    if self.nit == None:
                        self.nit = NitDecoder(bytes)
                        if self.nit.isValid(): self.createInfoTXT()
                    elif not self.nit.isValid():
                        self.nit = NitDecoder(bytes)
                        if self.nit.isValid(): self.createInfoTXT()
            elif pid ==17:
                if header['payload_unit_start_indicator'] == 1:
                    if self.sdt == None:
                        self.sdt = StdDecoder(bytes)
                    elif not self.sdt.isValid():
                        self.sdt = StdDecoder(bytes)
                elif self.sdt != None and not self.sdt.isValid():
                    self.sdt.readNext(bytes)
                if not self.structureReady and self.sdt !=None and self.pat !=None and self.sdt.isValid() and self.pat.isValid(): self.createFolderStructure()
            elif pid == 18: #EIT
                pass
            elif pid == 20: #TDT/TOT
                pass
            elif pid == 21: #network synchronization
                pass
            else: # Used by DVB metadata
                pass
        elif(pid>=32) and (pid <=8186):
            if pid in self.chanel: #audio or video channel
                if self.chanel[pid]['object'] == None:
                    if self.chanel[pid]['video']:
                        self.chanel[pid]['object'] = VideoDecoder(bits, self.chanel[pid]['path'])
                    elif self.chanel[pid]['audio']:
                        self.chanel[pid]['object'] = AudioDecoder(bits, self.chanel[pid]['path'])
                else:
                    self.chanel[pid]['object'].addData(bits)
                self.chanel[pid]['counter'] = self.chanel[pid]['counter'] + 1
            elif pid in self.servicePID: #service channel
                pmt = PmtDecoder(bytes)
                if pmt.isValid():
                    if not self.servicePID[pid]['status']:
                        self.chanel[pmt.getAudioChanel()] = {'video':False,'audio':True,'path':self.servicePID[pid]['path'],'object':None,'counter':0,'bitrate':None,'pmtCounter':0}
                        self.chanel[pmt.getVideoChanel()] = {'video':True,'audio':False,'path':self.servicePID[pid]['path'],'object':None,'counter':0,'bitrate':None,'pmtCounter':0}
                        self.servicePID[pid]['status'] = True
                        for id in pmt.getOtherChanel():
                            self.chanel[id] = {'video':False,'audio':False,'path':None,'object':None,'counter':0,'bitrate':None, 'pmtCounter':0}
                    else:
                        for chanel in pmt.getAllChanel():
                            self.chanel[chanel]['pmtCounter'] = self.chanel[chanel]['pmtCounter'] +1
            elif pid in self.radioServicePID: #radio chanel
                pass
        elif pid==8187: #Used by DigiCipher 2/ATSC MGT metadata
            pass
        elif (pid>=8188) and (pid<=8190): #May be assigned as needed to Program Map Tables, elementary streams and other data tables
            pass
        elif pid == 8191: #Null Packet (used for fixed bandwidth padding)
            pass

    def readAdaptionField(self,pid,bytes):
        pass

    def createInfoTXT(self):
        '''
        Method create info.txt file
        :return: None
        '''
        if self.nit !=None:
            wrData = {'networkName':'','network_id':'','brandwidthValue':'','constellationValue':'','guard_intervalValue':'','code_rateValue':''}
            data = self.nit.getData()
            for x in data['DVBDescriptorTags']:
                if x['DVB_descriptor_tag'] == 64:
                    wrData['networkName'] = str(x['data'])
                    break
            for x in data['transport_stream_loop']:
                for y in x['DVBDescriptorTags']:
                    if y['DVB_descriptor_tag'] == 90:
                        wrData['brandwidthValue'] = str(y['data']['brandwidthValue'])
                        wrData['constellationValue'] = str(y['data']['constellationValue'])
                        wrData['guard_intervalValue'] = str(y['data']['guard_intervalValue'])
                        wrData['code_rateValue'] = str(y['data']['code_rateValue'])
                        break
            if data['network_id'] != None: wrData['network_id'] = str(data['network_id'])
            with open(os.path.join(self.folderName,'info.txt'),mode='w',encoding='utf-8') as info:
                info.write('Network name: '+wrData['networkName']+'\n')
                info.write('Network ID: '+wrData['network_id']+'\n')
                info.write('Bandwidth: '+wrData['brandwidthValue']+'\n')
                info.write('Constellation: '+wrData['constellationValue']+'\n')
                info.write('Guard interval: '+wrData['guard_intervalValue']+'\n')
                info.write('Code rate: '+wrData['code_rateValue']+'\n\n')

    def writeAudio(self):
        '''
        Method write all audio chanel to files
        :return: None
        '''
        for key in self.pidDict:
            if key in self.chanel:
                if self.chanel[key]['audio']:
                    self.chanel[key]['object'].saveAudio()

    def writePIDToInfoTXT(self):
        '''
        Method write PID and bitrate to info,txt
        :return: None
        '''
        items = {}
        import decimal
        streamRate = self.nit.getBitrate()
        for key in self.pidDict:
                items[key] = decimal.Decimal(((self.pidDict[key]['count']/self.packetNumber)
                                             *streamRate)/1000000).quantize(decimal.Decimal('0.01'),
                                                                            rounding=decimal.ROUND_HALF_UP)
        with open(os.path.join(self.folderName,'info.txt'),mode='a',encoding='utf-8') as info:
            info.write('Bitrate:\n')
            sortItems = sorted(items.items(), key=lambda tup: tup[0])
            sortItems = sorted(sortItems, key=lambda tup: tup[1], reverse=True)
            for item in sortItems:
                info.write(str('0x{0:04x}'.format(item[0])) + ' ' + str(item[1]) + ' Mbps\n')

    def createFolder(self, path, folder):
        '''
        Method create remove old and create new folder
        :param path: Path to output location
        :param folder: Name of folder
        :return: None
        '''
        if os.path.exists(os.path.join(path,folder)):
            import shutil
            shutil.rmtree(os.path.join(path,folder))
        os.mkdir(os.path.join(path,folder))

    def createFolderStructure(self):
        '''
        Method create output folder structure
        :return: None
        '''
        self.structureReady = True
        if self.pat != None and self.sdt != None:
            patData = self.pat.getData()
            sdtData = self.sdt.getData()
            for service in sdtData['data']:
                for program in patData['data']:
                    if service['service_id'] == program['program_number'] and service['service_type']==1:
                        self.createFolder(self.folderName,str('0x{0:04X}'.format(program['program_map_pid'])) +
                                          '-'+service['service_provider_name']+'-'+service['service_name'])
                        self.servicePID[program['program_map_pid']] = {'status':False,'path':
                            os.path.join(self.folderName,str('0x{0:04X}'.format(program['program_map_pid']))
                                         +'-'+service['service_provider_name']+'-'+service['service_name'])}
                        break
                    elif service['service_id'] == program['program_number'] and service['service_type']==2:
                        self.radioServicePID[program['program_map_pid']] = {'status':False}
                        break