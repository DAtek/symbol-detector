# Symbol detector
## Real-time shape detection with camera frame analysis, developed for my thesis.

## Operation
The program analyzes each frame and finds the pointer. It stores the pointer's coordinates
from appearing to disappearing in blocks. When a block is defined, it sends to detector worker.  
   
It was only tested on Ubuntu based linux, it may requires some minor modifications to run on windows.

## Requirements
- Python >= 3.7.0
- ```requirements.txt```

## Usage
- Find a lightning object that can be easily distinguished from the background.
- Plug in an USB camera.
- Run the ```main.py``` script.
- Go to ```Settings -> Camera probe``` and calibrate the camera.
  - Refresh the frame with ```r``` and adjust blur and exposition.
  - Find the center of the pointer
  - Left click
  - Find the border of the pointer
  - Right click
  - Middle click somewhere. If a red circle appears, the calculation was successful.
  - Press ```q```
  - If you want to improve your selection, press ```d``` and go from beginning. 
- Select the symbol set.
- Start the detection.