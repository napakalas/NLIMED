"""GENERAL CLASS: performing method used by all classes"""

from abc import ABCMeta, abstractmethod, ABC
import json
import os.path
import requests
from nltk.corpus import stopwords
from nltk.tree import ParentedTree
from SPARQLWrapper import SPARQLWrapper, JSON
import copy
import rdflib

class GeneralNLIMED(ABC):
    def __init__(self):
        self.currentPath = os.path.dirname(os.path.realpath(__file__))
        try:
            config = self._loadJson("config.txt")
            self.apikey = config['apikey']
            self.corenlp_home = config['corenlp-home']
        except:
            self.apikey = "no-api-key"
            self.corenlp_home = "/"
        self.oboUrl = "http://data.bioontology.org/ontologies/"

    def _loadJson(self, *paths):
        file = os.path.join(self.currentPath,*paths)
        isExist = os.path.exists(file)
        if isExist:
            with open(file, 'r') as fp:
                data = json.load(fp)
            return data
        else:
            return {}

    def _dumpJson(self, data, *paths):
        file = os.path.join(self.currentPath,*paths)
        with open(file, 'w') as fp:
            json.dump(data, fp)

    def _saveToFlatFile(self, data, *paths):
        file = os.path.join(self.currentPath,*paths)
        f = open(file, 'w+')
        for datum in data:
            f.write(str(datum).replace('\n', ' ').replace('\r', ' ') + '\n')
        f.close()

    def _loadFromFlatFile(self, *paths):
        file = os.path.join(self.currentPath,*paths)
        try:
            f = open(file, 'r')
            lines = f.readlines()
            f.close()
            return lines
        except:
            return []

    def _saveBinaryInteger(self, data, *paths):
        import struct
        file = os.path.join(self.currentPath,*paths)
        with open(file, "wb") as f:
            for x in data:
                f.write(struct.pack('i', x))  # 4bytes

    def _loadBinaryInteger(self, *paths):
        import struct
        file = os.path.join(self.currentPath,*paths)
        with open(file, 'rb') as f:
            bdata = []
            while True:
                bytes = f.read(4)
                if bytes == b'':
                    break
                else:
                    bdata.append(struct.unpack('i', bytes)[0])  # 4bytes
        return bdata
