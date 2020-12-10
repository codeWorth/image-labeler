This program allows a user to easily label a .jpg image with boxes. These boxes are then stored in the image metadata.
Specifically, their data is stored where an image comment could go, so if your image has a comment, this program will overwrite it!

The user first drags their image into the dropzone (or opens their file explorer). Then they are presented with the labeling interface.
Once they've labeled their image, they press "Download" to save the image with those label boxes saved in the metadata. Every time a label box
is added, modified, or removed, this change is saved to local storage in the browser. The user can see a list of saved label boxes by pressing
the "Open saves" button in the bottom right. Label boxes are saved by the name of the image they are attached to. Therefore, if you have two images
with the same name, you may lose labels for the old image when you begin modifying the new image. This will hopefully change in the future.

The user is given 4 tools:
1. (A)dd: add a new label box. The user will be prompted to give it a name.
2. (M)ove: move an existing bounding box
3. (R)esize: resize an existing bounding box
4. (D)elete: delete an existing bounding box

These tools are like tools in a paint program. You first select the tool, either by cliking its button or pressing the corresponding key.
Then you select the box you want to modify, and the tool is activated. You may also select a label box when no tool is active. At this time,
if you click a tool button, or press the corresponding key, the tool will activate on the selected label box.

This user interface is designed to be as quick as possible to work with once you understand it. It may seem slightly clunky at first,
but I feel that once the user is used to this interface, it will allow them to add, modify, and remove label boxes without the program getting
in the way.

Label boxes have a position, a size, a name, and a description. The description can be modified by:
1. Deselecting any active tool
2. Clicking the label box you want to modify
3. Clicking the button under the word "Selected:" in the rightmost column

Label box names may be no more than 255 characters. Label box descriptions may be no more than 65535 characters.

Do not resize your image after adding label boxes!! The boxes will all be out of position as a result. This
will hopefully change in the future.


Planned features:
	- .png support
	- Make it possible to get out of the labeling interface without refreshing
	- More flushed out "Saves" menu

Image metadata nitty gritty:
Header is:
1. 0xFFFE
2. Check code to reduce user comments interfering
3. Length of data chunk in bytes
4. Number of labels, unsigned short

Each label is:
1. Header string length, byte
2. Description string length, short
3. x position, unsigned short, relative to top left
4. y position, unsigned short, relative to top left
5. x width, unsigned short
6. y height, unsigned short
7. Label header, ascii char string
8. Label description, ascii char string