### Description
**napari-large-3d-vis** is a **napari** plugin which allows open and browse any size ome-zarr or tiff image. User specifies amount of memory program can use to not overexceed the RAM of machine.
Program uses Turntable camera from *vispy*. Higher (lower resolution) image pyramid levels are used to display 3D volume when camera is outside the volume and when inisde only subvolume with the size to not overexeed maximum allowed RAM size is cropped.
### Installation
**Napari** has to be pre-installed. Pull the folder wtih plugin and save it on your machine. To add the plugin to napari run
` pip install -e path/to/plugin/folder `
### Running
Open napari, go to *Plugins* -> *NL3Dvis*. In opened window provide path to your ome-zarr or tiff image file, specify maximum amount of RAM memory you want to be used by the plugin. Select colors for channels (up to 4 channels can be visualized), intensity range and mode of scene rendering.
Mode of scene rendering can be either *Manual* where user updates the scene by pressing button, either *Auto* - update of teh sce happens independently of user every 5 s, or *Autostop* - in this mode sce update happens only when user stopped at some position for more than 3 s.
Press "Run" to run visualisation program. New window (canvas) will appear. You can open several images in paralel in different windows and browse them independently.

While in the window - you can move around using mouse and zoom using mouse wheel. In order to update the scen you hav to press **u**. Currently chosen channel is displayed at the info box at bottom left corner. To change the channel press **c**. If you want to turn on/off current channel - press **s**. If you want to reduce/increase max intensity limit for the current channel press **z/x**
