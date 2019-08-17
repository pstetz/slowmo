import pydicom

class Dicom:
    def __init__(self, filepath):
        self.filepath = filepath
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