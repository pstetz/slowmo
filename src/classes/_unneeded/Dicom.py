"""
Imports
"""
import os
import pydicom


"""
Dicom
"""
class Dicom:
    """The summary line for a class docstring should fit on one line.

    If the class has public attributes, they may be documented here
    in an ``Attributes`` section and follow the same formatting as a
    function's ``Args`` section. Alternatively, attributes may be documented
    inline with the attribute's declaration (see __init__ method below).

    Properties created with the ``@property`` decorator should be documented
    in the property's getter method.

    Attributes:
        attr1 (str): Description of `attr1`.
        attr2 (:obj:`int`, optional): Description of `attr2`.

    """

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

