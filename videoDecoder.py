#!/usr/bin/env python3
import struct
import os
import re
__author__ = 'Jakub Pelikan'


class VideoDecoder():
    '''
    Class decode video packets form ts stream, and save video in m2v format to file.
    '''

    start_code = struct.pack('>L', 0b00000000000000000000000110110011)
    def __init__(self, bits, path):
        self.path = path
        self.search = False
        self.saveVideo(bits)

    def addData(self, bits):
        '''
        Method add video packet to m2vfile
        :param bytes: bits with video
        :return: None
        '''
        self.saveVideo(bits)

    def saveVideo(self,bits):
        '''
        Method save video packets to m2v files
        :return: None
        '''
        if not self.search:
            if self.start_code in bits:
                self.search = True
                bits = re.search(self.start_code+b'.*',bits).group(0)
            else:
                return
        with open(os.path.join(self.path,'video.m2v'), mode='ab') as file:
            file.write(bits)