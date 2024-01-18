"""
This module is an example of a barebones QWidget plugin for napari

It implements the Widget specification.
see: https://napari.org/stable/plugins/guides.html?#widgets

Replace code below according to your needs.
"""
import os
from typing import TYPE_CHECKING

import dask
import numpy as np
import tifffile
import zarr
from magicgui.widgets import FileEdit, Label, CheckBox, PushButton, SpinBox, Slider, ComboBox, RadioButtons
from qtpy.QtWidgets import QVBoxLayout, QWidget
from .vis3D_ch import main2 as vis3D
from napari._qt.qt_viewer import QtViewer
from napari.components import ViewerModel as Viewer
from napari._vispy import VispyCanvas
from superqt import QCollapsible

if TYPE_CHECKING:
    pass


class NL3DvisWidget(QWidget):
    def __init__(self, napari_viewer):
        super().__init__()
        self._viewer = napari_viewer
        #QVBoxLayout is for vertical box layout objects
        self.setLayout(QVBoxLayout())
        
        #button to path of the zarr file
        self.path_img = Label(value='select zarr file')
        self.layout().addWidget(self.path_img.native)
        self.target_file = FileEdit(mode='d')
        self.layout().addWidget(self.target_file.native)
        #button to path of the tiff file
        self.path_img_tiff = Label(value='or select tiff file')
        self.layout().addWidget(self.path_img_tiff.native)
        self.target_file_tiff = FileEdit(mode='r', filter= "*.tif")
        self.layout().addWidget(self.target_file_tiff.native)
        #number of Gb for RAM
        self.max_ram_label = Label(value='maximum RAM allowed, Gb')
        self.layout().addWidget(self.max_ram_label.native)
        self.max_ram = SpinBox(value=5, min = 1, max = 30)
        self.layout().addWidget(self.max_ram.native)
        #z-pyramids
        self.z_pyr = CheckBox(text='z pyramids')
        #checkbox
        self.layout().addWidget(self.z_pyr.native)
        
        #colormap for 4 channels
        
        self._collapse2 = QCollapsible('Choose colors for the channels', self)
        self.cmap_label1 = Label(value = 'Channel 1')
        self.cmap1 = ComboBox(value = 'None', choices = ['None', 'Red', 'Green', 'Blue', 'Yellow', 'Cyan', 'Magenta', 'White'])
        self.cmap_label2 = Label(value = 'Channel 2')
        self.cmap2 = ComboBox(value = 'None', choices = ['None', 'Red', 'Green', 'Blue', 'Yellow', 'Cyan', 'Magenta', 'White'])
        self.cmap_label3 = Label(value = 'Channel 3')
        self.cmap3 = ComboBox(value = 'None', choices = ['None', 'Red', 'Green', 'Blue', 'Yellow', 'Cyan', 'Magenta', 'White'])
        self.cmap_label4 = Label(value = 'Channel 4')
        self.cmap4 = ComboBox(value = 'None', choices = ['None', 'Red', 'Green', 'Blue', 'Yellow', 'Cyan', 'Magenta', 'White'])
        self._collapse2.addWidget(self.cmap_label1.native)        
        self._collapse2.addWidget(self.cmap1.native)
        self._collapse2.addWidget(self.cmap_label2.native)        
        self._collapse2.addWidget(self.cmap2.native)
        self._collapse2.addWidget(self.cmap_label3.native)        
        self._collapse2.addWidget(self.cmap3.native)
        self._collapse2.addWidget(self.cmap_label4.native)        
        self._collapse2.addWidget(self.cmap4.native)
        self.layout().addWidget(self._collapse2)

        
        
        
        
        
        #intensity limits
        self.min_int_label = Label(value='min intensity')
        self.layout().addWidget(self.min_int_label.native)
        self.min_int = Slider(value=100, min=0, max=65535)
        self.layout().addWidget(self.min_int.native)
        
        self.max_int_label = Label(value='max intensity')
        self.layout().addWidget(self.max_int_label.native)
        self.max_int = Slider(value=1000, min=0, max=65535)
        self.layout().addWidget(self.max_int.native)
        
        #methods of reading tiff
        self.method_vis_label = Label(value = 'visualization method')
        self.layout().addWidget(self.method_vis_label.native)
        self.method_vis = RadioButtons(value = 'Manual', choices = ['Manual', 'Auto (update every 5 s)', 'Autostop (updates if non moving for 3 s)'])
        self.layout().addWidget(self.method_vis.native)
        
        #information box
        text_info = ' u - update the scene \n c - change the channel \n s - turn on/off current channel \n z/x - decrease/increase maximum intensity for current channel '
        self.method_info_box = Label(value = text_info)
        self.layout().addWidget(self.method_info_box.native)
        
        self.load_button = PushButton(text='Run')
        self.load_button.clicked.connect(self.load_file)
        self.layout().addWidget(self.load_button.native)
        
        

    def load_file(self):
        #viewer = Viewer()
        #qt_viewer = QtViewer(viewer)
        
        z_pyr = False; 
        #timer_check()
        #vis3D()
        cmap_list = [self.cmap1.value, self.cmap2.value, self.cmap3.value, self.cmap4.value]
        vis3D(self.target_file.value, self.target_file_tiff.value, self.max_ram.value, self.min_int.value, self.max_int.value, cmap_list, self.method_vis.value, self.z_pyr)
