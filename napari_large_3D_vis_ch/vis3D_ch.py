import numpy as np
from vispy import app, scene, io, color
from vispy.visuals.filters.clipping_planes import PlanesClipper
from ome_zarr.io import parse_url, ZarrLocation
from ome_zarr.reader import Reader
import fire
import yaml
import path
from dask import delayed
from dask.dataframe import from_dask_array
from napari._vispy import VispyCanvas
from vispy.scene import SceneCanvas
from napari.components import ViewerModel
from skimage.io import imread
import tifffile
import zarr
import dask
import sys
from vispy.app import use_app, Timer
import gc
from vispy.scene.visuals import Text, Rectangle
from vispy.util.event import Event
import datetime
import os
from memory_profiler import memory_usage
import contextlib, io
##here we prepare canvas and specify other vispy things
import time
from itertools import repeat




        
                               
        
    
def check_all_elements_equal(lst):
    repeated = list(repeat(lst[0], len(lst)))
    return repeated == lst
        
def OpenImageZarr(filepath_zarr, filepath_tiff, cmap_label_list, max_NCh = 4):
    
    if len(str(filepath_zarr))>3:
        #at the moment I didnt change anything for ZARR regarding channels
        print('ZARRR')
        reader = Reader(parse_url(filepath_zarr))
        nodes = list(reader())
        image_node = nodes[0]
        dask_data_5c = image_node.data
        #getting metadata and axes
        axis = ''
        for name_ch in nodes[0].metadata['axes']:
            axis = axis + name_ch['name']
        ax_ch = axis.find('c'); ax_z = axis.find('z'); ax_t = axis.find('t')
        N_z = dask_data_5c[0].shape[ax_z]
        dask_data = []; cmap_list_updated = []
        #check if zarr file has already pyramids
        if len(dask_data_5c)>1:
            N_ch = dask_data_5c[0].shape[ax_ch];
            #if zarr already have pyramids
            for nch in range(N_ch):
                single_channel_data = []
                for npyr in range(len(dask_data_5c)):
                    data_ch_pyr = np.take(dask_data_5c[npyr], 0, axis = ax_t)
                    data_ch_pyr = np.take(data_ch_pyr, nch, axis = ax_ch-1)
                    #this part needed if there is no pyramidization in z channel
                    downscaled_array_z = np.linspace(0, N_z-1, num = int(N_z/2**npyr))
                    downscaled_array_z = downscaled_array_z.astype('uint16')
                    data_ch_pyr2 = np.take(data_ch_pyr, indices = downscaled_array_z, axis = ax_z-2)
                    single_channel_data.append(data_ch_pyr2)
                dask_data.append(single_channel_data)
                cmap_list_updated.append(cmap_label_list[nch])
        else:
            N_ch = dask_data_5c.shape[ax_ch];
            #if there are no pyramids yet
            for nch in range(N_ch):
                single_channel_data = []
                for npyr in range(5): #this is number of artificially created pyr levels
                    data_ch_pyr = np.take(dask_data_5c, 0, axis = ax_t)
                    data_ch_pyr = np.take(data_ch_pyr, nch, axis = ax_ch-1)
                    ax_x = axis.find('x'); ax_y = axis.find('y');
                    N_z = dask_data_5c.shape[ax_z]
                    downscaled_array_z = np.linspace(0, N_z-1, num = int(N_z/2**npyr))
                    downscaled_array_z = downscaled_array_z.astype('uint16')
                    data_ch_pyr = np.take(data_ch_pyr, indices = downscaled_array_z, axis = ax_z-2)
                    downscaled_array_x = np.linspace(0, N_x-1, num = int(N_x/2**npyr))
                    downscaled_array_x = downscaled_array_z.astype('uint16')
                    data_ch_pyr = np.take(data_ch_pyr, indices = downscaled_array_x, axis = ax_x-2)
                    downscaled_array_y = np.linspace(0, N_y-1, num = int(N_y/2**npyr))
                    downscaled_array_y = downscaled_array_y.astype('uint16')
                    data_ch_pyr = np.take(data_ch_pyr, indices = downscaled_array_y, axis = ax_y-2)
                    single_channel_data.append(data_ch_pyr2)
                dask_data.append(single_channel_data)
                cmap_list_updated.append(cmap_label_list[nch])
        #here i consider pyramid structure of zarr file, but only in yx plane (last two axis)
        #for i in range(len(dask_data_5c)):
        #    dask_data.append(dask_data_5c[i][0,0,::2**i,:,:])
    else:
        if len(str(filepath_tiff))>3:
            print('TIFFF')
            store = tifffile.imread(filepath_tiff, aszarr=True)
            cache = zarr.LRUStoreCache(store, max_size=2 ** 30)
            zobj = zarr.open(cache, mode='r')
            with tifffile.TiffFile(filepath_tiff) as tif:
                axes = tif.series[0].axes
                ax_ch = axes.find('C')
                N_ch = tif.series[0].shape[ax_ch]
                if N_ch > max_NCh: N_ch = max_NCh
            
            lazy_imread = delayed(imread)
            reader = lazy_imread(filepath_tiff)
            
            if 'multiscales' in zobj.attrs:
                #this part also has to be changed
                data = [zobj[int(dataset['path'])] for dataset in zobj.attrs['multiscales'][0]['datasets']]
                dask_data = [dask.array.from_zarr(z) for z in data]
            else:
                lazy_imread = delayed(imread)
                reader = lazy_imread(filepath_tiff)  # doesn't actually read the file
                data = dask.array.from_zarr(zobj)
                
                print(data.shape)
                dask_data = []; cmap_list_updated = []
                if ax_ch>-1:
                    for nch in range(N_ch):
                        if cmap_label_list[nch]!= 'None':
                            d = np.take(data, nch, axis = ax_ch)
                            print(d.shape)
                            dask_data.append([d, d[::2,::2, ::2], d[::4,::4, ::4], d[::8,::8, ::8], d[::16,::16, ::16], d[::32,::32,::32]])
                            cmap_list_updated.append(cmap_label_list[nch])
                else:
                    dask_data.append([data, data[::2,::2, ::2], data[::4,::4, ::4], data[::8,::8, ::8], data[::16,::16, ::16], data[::32,::32,::32]])
                    cmap_list_updated.append(cmap_label_list[0])
                    N_ch = 1
    if dask_data == []:
        print('Please choose colormaps for each channel!', file=sys.stderr)
            
    return dask_data, cmap_list_updated, N_ch

## here is a bunch of functions
def find_xyz_pos(r, theta, phi, volume_center):
    #input angles are in degrees, and we need radians!
    theta = (theta)/180*np.pi
    phi = (phi)/180*np.pi
    #print('volume center, find xyz: '+ str(volume_center))
    #z = int(r*np.cos(phi)*np.sin(theta)) + int(volume_center[2])
    z = (r*np.sin(theta)) + (volume_center[2])
    z_inv = (volume_center[2]*2)-z
    x = (r*np.cos(theta)*np.sin(phi)) + (volume_center[0])
    x_inv = (volume_center[0])*2 - x
    y = (r*np.cos(phi)*np.cos(theta)) + (volume_center[1])
    y_inv = (volume_center[1]*2)-y
    return x,y,z,x_inv,y_inv,z_inv

def determine_pyr_level(distance, NPyr, n_cur, shape_pyr_level_in):
    print('distance is ' + str(distance))
    print('NPyr ' + str(NPyr))
    shape_pyr_level = np.array(shape_pyr_level_in).copy(); 
    print('shape of the vol is ' + str(shape_pyr_level))
    FullRadius_pyrlevel = np.max(shape_pyr_level)/2 
    print('FullRadius_pyrlevel is ' + str(FullRadius_pyrlevel))
    
    relative_distance = distance/FullRadius_pyrlevel #[0,1]
    print('NPyr is: ' + str(NPyr))
    print('Relative distance is ' + str(relative_distance))
    new_pyr_level = int((relative_distance-1)*NPyr)-1
    print('new pyr level is ' + str(new_pyr_level))
    if new_pyr_level<1:
        new_pyr_level=1
    if new_pyr_level>=NPyr:
        new_pyr_level = NPyr-1
    return new_pyr_level

def print_update_text(canvas, now, rect_position, rect_size, t=None):
    text = 'Scene updated at ' + str(now)[11:-7]
    col = np.array([200, 200, 0])/255 #dark yellow
    if t == None:
        t = Text(text, parent=canvas.scene, color=col, font_size=11, pos = (rect_position[0]+rect_size[0]//10, rect_position[1]+rect_size[1]//3))
    else:
        t.text = text; t.pos = (rect_position[0]+rect_size[0]//10, rect_position[1]+rect_size[1]//3)
    return t

def print_mem_usage_text(canvas, mem_used, rect_position, rect_size, t=None):
    text = 'Used RAM, Mb: ' + str(mem_used)
    col = np.array([18, 255, 247])/255 #cyan
    if t == None:
        t = Text(text, parent=canvas.scene, color=col, font_size=11, pos = (rect_position[0]+rect_size[0]//10, rect_position[1]+rect_size[1]//4.2))
    else:
        t.text = text; t.pos = (rect_position[0]+rect_size[0]//10, rect_position[1]+rect_size[1]//4.2)
    return t

def print_max_int_text(canvas, volume, cmap_label_list, cur_ch, rect_position, rect_size, t=None):
    max_int = volume[cur_ch].clim[1]
    text = 'Channel ' + str(cur_ch) + ' \n Maximum Intensity: ' + str(int(max_int))
    #print(cmap_label_list[cur_ch])
    if cmap_label_list[cur_ch][0] == 'R': col = np.array([1,0,0])
    if cmap_label_list[cur_ch][0] == 'G': col = np.array([0,1,0])
    if cmap_label_list[cur_ch][0] == 'B': col = np.array([0,0,1])
    if cmap_label_list[cur_ch][0] == 'Y': col = np.array([1,1,0])
    if cmap_label_list[cur_ch][0] == 'C': col = np.array([0,1,1])
    if cmap_label_list[cur_ch][0] == 'M': col = np.array([1,0,1])
    if cmap_label_list[cur_ch][0] == 'W': col = np.array([1,1,1])
    if t == None:
        t = Text(text, parent=canvas.scene, color=col, font_size=11, pos = (rect_position[0]+rect_size[0]//10, rect_position[1]+rect_size[1]//12))
    else:
        t.text = text; t.pos = (rect_position[0]+rect_size[0]//10, rect_position[1]+rect_size[1]//12); t.color = col
    return t


def print_xyz_text(canvas, x, y, z, rect_position, rect_size, t=None):
    text = 'x: ' + str(x) + '\n' + 'y: ' + str(y) + '\n' + 'z: ' + str(z) + '\n'
    col = np.array([200, 0, 0])/255 #dark red
    if t == None:
        t = Text(text, parent=canvas.scene, color=col, font_size=14, pos = (rect_position[0]+rect_size[0]//10, rect_position[1]-rect_size[1]//3.8), bold = True)
    else:
        t.text = text; t.pos = (rect_position[0]+rect_size[0]//10, rect_position[1]-rect_size[1]//3.8)
    return t

def CheckIfInside(x,y,z, vol_shape):
    #print('x_inv, y, z')
    #print(x)
    #print(y)
    #print(z)
    #print('Vol shape is: ' + str(vol_shape))
    if x>0 and x<vol_shape[2] and y>0 and y<vol_shape[1] and z>0 and z<vol_shape[0]:
        isinside = True
    else:
        isinside = False
    return isinside

def extract_subset(dask_data, x, y, z, vol_shape, volume_center, boxsize):
    #print(vol_shape)
    #we consider only the lowest level of pyramid - higher resolution
    dask_array = dask_data[0]
    # if we are inside the volume - crop only part of it
    x0 = int(x - boxsize/2); x1 = int(x + boxsize/2)
    y0 = int(y - boxsize/2); y1 = int(y + boxsize/2)
    z0 = int(z - boxsize/2); z1 = int(z + boxsize/2)
    #boundaries check
    if x0<0: 
        x0=0; x1 = boxsize
    if x1>vol_shape[2]: 
        x1=vol_shape[2]; x0 = x1-boxsize
    if y0<0: 
        y0=0; y1 = boxsize
    if y1>vol_shape[1]: 
        y1=vol_shape[1]; y0 = y1-boxsize
    if z0<0: 
        z0=0; z1 = boxsize
    if z1>vol_shape[0]: 
        z1=vol_shape[0]; z0 = z1-boxsize
    np_list_of_chunks = []
    for nch in range(len(dask_array)):
        chunk = dask_array[nch][z0:z1, y0:y1, x0:x1]
        np_chunk = chunk.compute()
        np_list_of_chunks.append(np_chunk)
        del np_chunk
    return np_list_of_chunks

def DetBoxSizeMem(dask_array, max_mem_allowed):
    dtype = str(dask_array.dtype)
    if dtype[-2] == 'u1':
        n_bytes = 1
    elif dtype[-2] == 'u2':
        n_bytes = 2
    elif dtype[-2] == 'u4':
        n_bytes = 4
    else:
        n_bytes = 8
    n_pixels_max = max_mem_allowed/n_bytes*(2**30)
    boxsize = np.floor(n_pixels_max**(1/3))    
    return int(boxsize)
    

def CheckMemory(dask_array, NCh, cur_pyr_level, max_mem_allowed):
    dtype = str(dask_array[0][cur_pyr_level].dtype)
    if dtype[-2] == 'u1':
        n_bytes = 1
    elif dtype[-2] == 'u2':
        n_bytes = 2
    elif dtype[-2] == 'u4':
        n_bytes = 4
    else:
        n_bytes = 8
    #print('Computed size of the level image (Gb) is: ' + str(NGb))    
    if dask_array[0][cur_pyr_level].size*NCh*n_bytes<max_mem_allowed*(2**30):
        allowed = True
    else:
        allowed = False
        
    return allowed
    
def timer_func(some_text, event):
    print('timer_func')
    print(some_text)

def get_canvas_name(path_img_in, path_img_in_tiff):
    if len(str(path_img_in))>2:
        try:
            canvas_name = str(path_img_in).split("/")[-2]
        except:
            canvas_name = str(path_img_in).split("\\")[-2] 
    elif len(str(path_img_in_tiff))>2:
        canvas_name = os.path.basename(path_img_in_tiff)
    else: 
        print('Please enter a valid path for zarr or tiff image, cause Im confused:(', file=sys.stderr)
    return canvas_name      


        
class MyCanvas(SceneCanvas):
    def __init__(self, canvas_title, clim, cmap_label, max_mem, dask_data, method_vis, Nch):
        SceneCanvas.__init__(self, keys='interactive', size=(800, 600), title = canvas_title, show = True)
        #self.canvas = SceneCanvas(keys='interactive', size=(800, 600), title = canvas_title, show = True)
        self.measure_fps()
        self.unfreeze()
        self.view = self.central_widget.add_view()
        self.Nch = Nch
        self.prev_clim_max = np.zeros((Nch))
        self.view.camera = scene.TurntableCamera()
        self.dask_data = dask_data; self.clim = clim; self.cmap_label_list = cmap_label; self.max_memory = max_mem
        self.rect = None; self.text_time_upd = None; self.text_mem_used = None; self.text_max_int = None; self.text_xyz = None
        self.x_list = []; self.y_list = []; self.z_list = []
        #self.app = app.application.Application()
        self.pyr_level = len(dask_data[0])-1; self.vol_shape = dask_data[0][-1].shape
        self.method_vis = method_vis; self.fps_prev = self.fps
        self._initialize_volume()
        self.timer = app.Timer(0.5, connect=self.on_time, start=True)
        self.timer_close = app.Timer(15, connect=self.check_canvas_closed, start=True)
        if method_vis[:5] == 'Auto ':
            self.timer_slow = app.Timer(5, connect=self.update_whole_scene, start=True)
        
        
        self.run_program = True
    
    def _initialize_volume(self):
        print('init volume')
        
        vol_init = [self.dask_data[i][-1] for i in range(len(self.dask_data))]
        vol_init_np = [d.compute() for d in vol_init]
        
        print('np_chunk0 shape is: ' + str(vol_init_np[0].shape))
        #print('full volume shape is: ' + str(self.dask_data[0].shape))
        
        self.volume_list = self.update_volume_multichannel(vol_init_np, [])
        self.cur_ch = 0
        self.NCh = len(vol_init_np)
        
        volume_center = (np.array(vol_init_np[0].shape) / 2)[::-1]
        #set volume center and initial camera position
        self.view.camera._actual_distance = np.max(vol_init_np[0].shape)*2; self.view.camera.distance = self.view.camera._actual_distance
        self.view.camera.center = volume_center
        
    def on_time(self, event):
        
        ## draw info box first
        color_box = [0.2, 0.2, 0.2]; color_box_border = [1, 1, 1]
        if self.rect == None: 
            self.rect = Rectangle(center=(self.size[0] // 10, self.size[1] // 10*9), width=self.size[1] // 5*2, height=self.size[0] // 5, color=color_box, border_color=color_box, radius=0.02, parent=self.scene)
        else:
            self.rect.center = (self.size[0] // 10, self.size[1] // 10*9)
        rcenter = self.rect.center; rsize = (self.rect.width, self.rect.height)
        
        #print update time
        time_update = datetime.datetime.now()
        if self.text_time_upd == None:
            self.text_time_upd = print_update_text(self, time_update, rcenter, rsize)
        else:
            self.text_time_upd = print_update_text(self, time_update, rcenter, rsize, self.text_time_upd)
        #print memory usage
        mem_usage = memory_usage(-1, interval=.01, timeout=None); mem_usage = int(mem_usage[0])
        if self.text_mem_used == None:
            self.text_mem_used = print_mem_usage_text(self, mem_usage, rcenter, rsize)
        else:
            self.text_mem_used = print_mem_usage_text(self, mem_usage, rcenter, rsize,  self.text_mem_used)
        #print max intensity value
        if self.text_max_int == None:
            self.text_max_int = print_max_int_text(self, self.volume_list, self.cmap_label_list, self.cur_ch, rcenter, rsize)
        else:
            self.text_max_int = print_max_int_text(self, self.volume_list, self.cmap_label_list, self.cur_ch, rcenter, rsize,  self.text_max_int) 
        #print x,y,z positions
        volume_center = (np.array(self.vol_shape)/ 2)[::-1]
        x,y,z,x_inv,y_inv, z_inv = find_xyz_pos(self.view.camera._actual_distance, self.view.camera.elevation, self.view.camera.azimuth, volume_center)
        coef = 2**(self.pyr_level); 
        x*=coef;y*=coef;z*=coef;x_inv*=coef;y_inv*=coef; z_inv*=coef
        if self.text_xyz == None:
            self.text_xyz = print_xyz_text(self, int(x), int(y), int(z), rcenter, rsize)
        else:
            self.text_xyz = print_xyz_text(self, int(x), int(y), int(z), rcenter, rsize, self.text_xyz) 
        
        ##test part
        '''
        print('volume_shape')
        q = self.show
        print(self.vol_shape)
        print(self.size)
        print(self.app)
        print(self.shared)
        print(self.parent)
        '''
        ## this part works only in autostop mode
        if self.method_vis[:8] == 'Autostop':
            n_time_points = 7
            self.x_list.append(x); self.y_list.append(y); self.z_list.append(z);
            if len(self.x_list)>=n_time_points:
                self.x_list = self.x_list[-n_time_points:]
                self.y_list = self.y_list[-n_time_points:]
                self.z_list = self.z_list[-n_time_points:];
                if check_all_elements_equal(self.x_list) and check_all_elements_equal(self.y_list) and check_all_elements_equal(self.z_list):
                    self.update_whole_scene()
                    self.x_list = []; self.y_list = []; self.z_list = []
                
                
    def update_volume_multichannel(self, np_array_list, volume_list):
    
        parent_scene = self.view.scene
        cmap_label_list = self.cmap_label_list; clim = self.clim
        if volume_list == []:
            for nch in range(self.Nch):
                cmap_label_list[nch]
                if cmap_label_list[nch][0] == 'R': colors_cmap = np.array([[0,0,0],[1,0,0]])
                if cmap_label_list[nch][0] == 'G': colors_cmap = np.array([[0,0,0],[0,1,0]])
                if cmap_label_list[nch][0] == 'B': colors_cmap = np.array([[0,0,0],[0,0,1]])
                if cmap_label_list[nch][0] == 'Y': colors_cmap = np.array([[0,0,0],[1,1,0]])
                if cmap_label_list[nch][0] == 'C': colors_cmap = np.array([[0,0,0],[0,1,1]])
                if cmap_label_list[nch][0] == 'M': colors_cmap = np.array([[0,0,0],[1,0,1]])
                if cmap_label_list[nch][0] == 'W': colors_cmap = np.array([[0,0,0],[1,1,1]])
                
                custom_cmap = color.colormap.Colormap(colors = colors_cmap)
                v = scene.visuals.Volume(np_array_list[nch], cmap=custom_cmap, method='mip', raycasting_mode='volume', gamma="1.0", interpolation='linear', parent=parent_scene, clim = clim)
                volume_list.append(v)
                v.set_gl_state(preset='additive')
                v.opacity = 1/len(np_array_list)
        else:
            for nch in range(self.Nch):
                volume_list[nch].set_data(np_array_list[nch])
            
        return volume_list            
    
    def update_actual_scene_inside(self, np_list_of_chunks, n_pyr_cur, volume_center, boxsize, x, y, z):
        #print('xyz-inside')
        #print(x)
        #print(y)
        #print(z)
        self.volume_list = self.update_volume_multichannel(np_list_of_chunks, self.volume_list) 
        distance = volume_center - np.array([x,y,z])
        chunk_center = np.array([boxsize/2, boxsize/2, boxsize/2])
        print('cam center before update: ' + str(self.view.camera.center))
        print('distance vector is : ' + str(distance))
        print('volume_center is : ' + str(volume_center))
        self.view.camera.center = (chunk_center + distance)#[::-1]
        #cam.scale_factor *= 2**(n_pyr_cur-new_pyr_level)
        self.view.camera._actual_distance *= 2**(n_pyr_cur-self.pyr_level)
        self.view.camera.distance = self.view.camera._actual_distance
        print('cam center after update: ' + str(self.view.camera.center))
        gc.collect()
        
    def update_actual_scene_outside(self, old_pyr_level):
        volume_np_list = []
        for nch in range(self.NCh):
            volume_da = self.dask_data[nch][self.pyr_level]
            volume_np_list.append(volume_da[:,:,:].compute())
        
        self.volume_list = self.update_volume_multichannel(volume_np_list, self.volume_list)
        volume_center = (np.array(self.vol_shape)/ 2)[::-1]
        #print('Volume np shape is: ' + str(volume_np.shape))
        print('Volume center is: ' + str(volume_center))
        self.view.camera.center = volume_center
        #cam.scale_factor *= 2**(n_pyr_cur-new_pyr_level)
        self.view.camera._actual_distance *= 2**(old_pyr_level-self.pyr_level)
        self.view.camera.distance = self.view.camera._actual_distance
        gc.collect()
    
    def update_whole_scene(self, boxsize=200):
        #find position in a current pyr level
        print('update_whole_scene')
        print(self.vol_shape)
        volume_center = (np.array(self.vol_shape)/ 2)[::-1]
        
        x,y,z,x_inv,y_inv, z_inv = find_xyz_pos(self.view.camera._actual_distance, self.view.camera.elevation, self.view.camera.azimuth, volume_center)
        print('xyz')
        print(x)
        print(y)
        print(z)
        #print('x_inv, y_inv, z_inv')
        #print(x_inv)
        #print(y_inv)
        #print(z_inv)
        inside = CheckIfInside(x_inv, y, z, self.vol_shape)
        print('Inside is: ' + str(inside))
        n_pyr_cur = self.pyr_level
        if not inside:
            new_pyr_level = determine_pyr_level(self.view.camera._actual_distance, len(self.dask_data[0]), self.pyr_level, self.vol_shape)
            print('Current pyr level ' + str(self.pyr_level))
            print('Try new pyr level ' + str(new_pyr_level))
            allowed_mem = False; new_pyr_level -= 1
            while allowed_mem == False:
                new_pyr_level += 1
                allowed_mem = CheckMemory(self.dask_data, self.NCh, new_pyr_level, self.max_memory/2)
            #print('Cur pyr level' + str(n_pyr_cur))
            print('Updated new pyr level ' + str(new_pyr_level))
            if new_pyr_level != n_pyr_cur:
                coef = 2**(n_pyr_cur-new_pyr_level)
                x*=coef;y*=coef;z*=coef;x_inv*=coef;y_inv*=coef; z_inv*=coef      
                self.pyr_level = new_pyr_level
                self.vol_shape = np.array(self.dask_data[0][new_pyr_level].shape)
                print('volume shape is: ' + str(self.vol_shape))
                self.update_actual_scene_outside(n_pyr_cur)

        if inside:
            new_pyr_level = 0
            boxsize = DetBoxSizeMem(self.dask_data[0][new_pyr_level], self.max_memory/2)
            boxsize /= len(self.dask_data)**(1/3)
            print('Computed box size: ' + str(boxsize))
            #boxsize = 500
            if new_pyr_level != n_pyr_cur:
                coef = 2**(n_pyr_cur-new_pyr_level)
                x*=coef;y*=coef;z*=coef; x_inv*=coef; y_inv*=coef; z_inv*=coef       
                self.pyr_level = new_pyr_level
                self.vol_shape = np.array(self.dask_data[0][new_pyr_level].shape)
                volume_center = (np.array(self.vol_shape)/ 2)[::-1]
                '''
                if not z_pyr:
                    volume_center[2] /= 2**new_pyr_level
                    CS.vol_shape[0] /= 2**new_pyr_level
                '''
                #print('Boxsize is ' + str(boxsize))
            np_list_of_chunks = extract_subset(self.dask_data, x, y_inv, z, self.vol_shape, volume_center, boxsize)   
            self.update_actual_scene_inside(np_list_of_chunks, n_pyr_cur, volume_center, boxsize, x, y_inv, z)
            
    def change_max_int(self, mode):
        
        if self.pyr_level == 0:
                step_int = 1000
        elif self.pyr_level == 1 or self.pyr_level == 2:
            step_int = 500
        else:
            step_int = 100
        clim_cur = list(self.volume_list[self.cur_ch].clim)
        print(clim_cur)
        if mode == 'up':
            self.volume_list[self.cur_ch].clim = [clim_cur[0], clim_cur[1]+step_int]
        if mode == 'down':
            if clim_cur[1]>step_int:
                self.volume_list[self.cur_ch].clim = [clim_cur[0], clim_cur[1]-step_int]     
    
    def change_channel(self):
        cur_ch = self.cur_ch+1
        if cur_ch > self.NCh-1: cur_ch = 0
        self.cur_ch = cur_ch
    
    def on_off_channel(self):
        cur_ch = int(self.cur_ch)
        clim_cur = list(self.volume_list[cur_ch].clim)
        if clim_cur[0] == clim_cur[1]:
            self.volume_list[cur_ch].clim = [clim_cur[0], self.prev_clim_max[cur_ch]]
        else:
            self.prev_clim_max[cur_ch] = clim_cur[1]
            self.volume_list[cur_ch].clim = [clim_cur[0], clim_cur[0]]
    
    def check_canvas_closed(self, event):
    #here i check fps and if it is exactly the same as previous one - then it means that canvas window is closed
        self.fps_cur = self.fps
        print(self.fps_prev)
        #print(fps_cur)
        if self.fps_cur != self.fps_prev:
            print('canvas is open')
            self.fps_prev = self.fps_cur
        else:
            print('canvas is closed')
            self.timer_close.stop()
            self.timer.stop()
            self.close()
            self.run_program = False
            #exit()
            #sys.exit(0)
            #stop_program = True

            #del canvas
            #app.quit() #this closes napari
            #sys.exit('canvas was closed')

def main2(path_img_in, path_img_in_tiff, max_memory_in, cmin, cmax, cmap_label_list, method_vis):
    #path_img_in, path_img_in_tiff, max_memory_in, z_pyr_in, cmin, cmax, cmap_label, method_tiff

    
    #global timer_info_box, timer_check_canvas_closed
    #timer_info_box = Timer(1, connect=info_box, start=True)
    #timer_check_canvas_closed = Timer(5, connect=check_canvas_closed, start=True)
    
    #global view, cam, canvas, render_method_list, volume, dask_data
    canvas_title = get_canvas_name(path_img_in, path_img_in_tiff)
    c_lim = [cmin, cmax]
    dask_data, cmap_label_list_final, Nch = OpenImageZarr(path_img_in, path_img_in_tiff, cmap_label_list)
    my_canvas = MyCanvas(canvas_title, c_lim, cmap_label_list_final, max_memory_in, dask_data, method_vis, Nch)
    view = my_canvas.view; cam = view.camera
    #print('mycanva_run: ' + str(my_canvas.run_program))
    #while my_canvas.run_program == True:
    
    @my_canvas.events.key_press.connect
    def on_key_press(event):
        if event.text == 'u':

            #Event(write_text_on_canvas('Updating scene...'))
            #t_canvas = write_text_on_canvas('Updating scene...')
            print('Camera distance, actual distance, elevation, azimuth before update')
            print(cam.distance)
            print(cam._actual_distance)
            print(cam.elevation)
            print(cam.azimuth)
            print('UPDATE BUTTON PRESSED')
            my_canvas.update_whole_scene()
            print('Camera distance, actual distance, elevation, azimuth after update')
            print(cam.distance)
            print(cam._actual_distance)
            print(cam.elevation)
            print(cam.azimuth)

            #tt = print_update_text(ttt)


        #change max intensity limit
        if event.text == 'x':
            my_canvas.change_max_int('up')

        if event.text == 'z':
            my_canvas.change_max_int('down')
        #change channel    
        if event.text == 'c':
            my_canvas.change_channel()
        #turn on/off the channel 
        if event.text == 's':
            my_canvas.on_off_channel()
        
    #app.run()
    
    
if __name__ == "__main__":
    fire.Fire(main2)
    

    
