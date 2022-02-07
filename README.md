# Symbol detector
## Real-time shape detection with camera frame analysis.

This program was developed for my thesis in 2017 and the repo contains just a slightly modified version.  

In that time I had no concept about _TDD_ and _Clean Code_, that's why the code is messy and doesn't have tests.

## Operation
The program analyzes each frame and finds the pointer. It stores the pointer's coordinates
from appearing to disappearing in blocks. When a block is defined, it sends to detector worker.  
   
It was only tested on Ubuntu based linux, it may require some minor modifications to run on Windows.

## Requirements
- `python >= 3.8.0`
- `poetry`
- `tcl/tk`

## Usage
- Create a `python` virtual environment.
- Activate the environment and run `poetry install`.
- Find an illuminating object that can be easily distinguished from the background.
- Make sure that you have a camera.
- Run `symbol-detector-gui` script.
- Go to `Settings -> Camera probe` and calibrate the camera. The calibration is correct when only the expected object (_pointer_) can be shown on the screen.
  - Refresh the frame with `r` and adjust blur and exposition.
  - Find the center of the pointer
  - Left click
  - Find the border of the pointer
  - Right click
  - Middle click somewhere. If a red circle appears, the calculation was successful.
  - Press `q`
  - If you want to improve your selection, press `d` and go from beginning. 
- Select the symbol set.
- Start the detection.