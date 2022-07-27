
- [Virtual mouse](#virtual-mouse)
  - [Features](#features)
  - [Installation](#installation)
  - [Guide](#guide)
  - [Gestures](#gestures)

# Virtual mouse

## Features

- Accurate
- Fast
- Adaptive
- Smooth
- User authentication
- Auditory feedback


## Installation

- Create a python 3.8 environment
- Install the required python packages  
    `pip3 install -r requirments.txt`
- Activate the environment
- Make sure to put a photo of yours replacing `DiaaEldeen.jpg` photo inside the root folder to be used for authentication
- You need to provide your webcam steaming IP address by writing it to the `streaming_device` variable inside `VideoCapture.py` file, Or you can set it to 0 or 1 to use Laptop's camera
- Start the application  
    `python3 VirtualMouse.py`



## Guide
- The application will take some time after launching it to authenticate your face
- Raise your Right hand with all fingers open to unlock the mouse
- Use gestures to control the mouse

## Gestures
- Palm (All fingers open) -> Unlock the mouse
- Fist (All fingers closed) -> Lock the mouse
- Index and Middle fingers are up, and the rest are closed -> Mouse pointer movement mode
- Index finger clicks the thumb while in the mouse pointer movement mode -> Left click
- Middle finger clicks the thumb while in the mouse pointer movement mode -> Right click