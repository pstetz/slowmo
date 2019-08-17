import os
import pydicom
from glob import glob
from os.path import join

class DicomDir:
    def __init__(self, filepath):
        self.directory = filepath
        self.load_dicoms()
        
    def load_dicoms(self):
        dicoms, sheets = list(), list()
        self.num_volumes = 0
        first_loc = None
        di
        for dicom_path in glob(join(self.directory, "*")):
            dicom = Dicom(dicom_path)
            if first_loc is None:
                first_loc = dicom.slice_loc

            sheets.append({
                "slice_loc": dicom.slice_loc,
                "trigger_time": dicom.trigger_time,
                "dicom": dicom
            })
            
            if first_loc == dicom.slice_loc: # be careful of last volume
                volume = {"volume": self.num_volumes, "sheets": sheets}
                self.num_volumes += 1
                dicoms.append(volume)
                sheets = list()
        self.dicoms = dicoms
        return dicoms

class Dicom:
    def __init__(self, filepath):
        self.filepath = filepath
        self.name     = os.path.basename(filepath)
        self.load()
        self.get_data()
        self.get_slice_loc()
        self.get_trigger_time()
        
    def load(self):
        dicom = pydicom.read_file(self.filepath)
        self.dicom = dicom
        return dicom
    
    def get_data(self):
        data = self.dicom.pixel_array
        self.data = data
        return data
    
    def get_slice_loc(self):
        slice_loc = self.dicom.SliceLocation
        self.slice_loc = slice_loc
        return slice_loc
    
    def get_trigger_time(self):
        trigger_time = self.dicom.TriggerTime
        self.trigger_time = trigger_time
        return trigger_time