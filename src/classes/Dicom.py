"""
Imports
"""
import os
import shutil
import pydicom
import zipfile
import numpy as np
from tqdm import tqdm
from glob import glob
from os.path import join


"""
DicomDir
"""
class DicomDir:
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
        if filepath.endswith(".zip"):
            filepath = self._unzip_rm(filepath)
        self.directory = filepath
        print("loading dicoms from %s..." % filepath)
        self.load_dicoms()

    def get_volume(self, index):
        volume_data = list()

        ### Load and sort relevant sheets
        volume = self.dicoms[index]
        sheets = volume["sheets"]
        sheets = sorted(sheets, key=lambda x: -x["slice_loc"]) # Checked -slice_loc is correct (minus important!)

        ### Load data from sheets
        for sheet in sheets:
            volume_data.append(sheet["dicom"].data)

        volume_data = np.array(volume_data)
        volume_data = self._reshape(volume_data)
        return volume_data

    def _reshape(self, data, new_shape = (74, 74, 45)):
        reshaped = np.zeros(new_shape)
        assert data.shape == (45, 74, 74), "Expected shape (45, 74, 74), found shape %s" % str(data.shape)
        for i in range(data.shape[0]):
            reshaped[:, :, i] = data[i, :, :]
        return reshaped

    def _sort_by_trigger_time(self):
        print("Sorting dicoms by trigger time...")
        sorted_dicoms_dict = list()
        for dicom_path in tqdm(glob(join(self.directory, "*"))):
            dicom = Dicom(dicom_path)
            d = {"trigger_time": dicom.trigger_time, "dicom": dicom}
            sorted_dicoms_dict.append(d)
        sorted_dicoms_dict = sorted(sorted_dicoms_dict, key=lambda k: k["trigger_time"])
        sorted_dicoms = [dicom["dicom"] for dicom in sorted_dicoms_dict]
        return sorted_dicoms

    def load_dicoms(self):
        """
        NOTE: it may be too memory intensive to keep all the dicoms in memory.
        Especially when the model is running
        """
        dicoms, sheets = list(), list()
        self.num_volumes = 0
        first_loc = None

        ### Load all of the available dicoms in the path
        dicoms_sorted = self._sort_by_trigger_time()
        for dicom in tqdm(dicoms_sorted):
            if first_loc is None:
                first_loc = dicom.slice_loc
            elif dicom.slice_loc == first_loc:
                volume = {"volume": self.num_volumes, "sheets": sheets}
                self.num_volumes += 1
                dicoms.append(volume)
                sheets = list()

            sheets.append({
                "slice_loc": dicom.slice_loc,
                "trigger_time": dicom.trigger_time,
                "dicom": dicom
            })

        ### Load the final sheet
        if sheets:
            volume = {"volume": self.num_volumes, "sheets": sheets}
            self.num_volumes += 1
            dicoms.append(volume)

        ### Set the dicoms variable and return
        self.dicoms = dicoms
        return dicoms

    def _cut_volumes(self, num_volumes):
        assert num_volumes < len(self.num_volumes), "Cannot cut %d volumes when only %d exist!" % (num_volumes, self.num_volumes)
        self.dicoms = self.dicoms[num_volumes:]
        self.num_volumes -= num_volumes
        return self.dicoms


    """
    Helpers
    """
    def _unzip_rm(self, zip_path):
        print("unzipping %s..." % zip_path)
        new_path = self._unzip(zip_path)
        print("removing old path %s..." % zip_path)
        self._rm(zip_path)
        return new_path

    def _rm(self, filepath):
        if os.path.isfile(filepath):
            os.remove(filepath)
        elif os.path.isdir(filepath):
            shutil.rmtree(filepath)
        else:
            raise Exception("Cannot rm %s" % filepath)

    def _unzip(self, zip_path):
        ### Set new name
        dcm_folder = os.path.dirname(zip_path)
        dcm_name = os.path.basename(zip_path).split(".")[0]
        unzip_path = join(dcm_folder, dcm_name)

        ### Unzip and add to paths
        z_file = zipfile.ZipFile(zip_path)
        z_file.extractall(unzip_path)

        ### Move all dcm to dcm_path
        self._format_dcm_folder(unzip_path)

        return unzip_path

    def _format_dcm_folder(self, dcm_folder):
        """ Move all the dicoms from inner folders to dcm_folder"""
        items = glob(join(dcm_folder, "*"))
        if all([os.path.isfile(item) for item in items]):
            return
        for item in items:
            if os.path.isfile(item):
                continue
            inner_items = glob(join(item, "*"))
            if len(inner_items) == 0:
                shutil.rmtree(item)
            for inner_item in inner_items:
                item_name = os.path.basename(inner_item)
                os.rename(inner_item, join(dcm_folder, item_name))
        self._format_dcm_folder(dcm_folder)


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

