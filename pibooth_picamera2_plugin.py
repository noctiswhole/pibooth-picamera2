try:
    import pibooth
except Exception as e:
    print(e)
    exit()
from rpi_picamera2 import Rpi_Picamera2, get_rpi_picamera2_proxy

# This hook returns the custom camera proxy.
# It is defined here because yield statement in a hookwrapper with a 
# similar name is used to invoke it later. But check first if other cameras
# are installed or if the user specifically asks for this
@pibooth.hookimpl
def pibooth_setup_camera():
    rpi_picamera2_proxy = get_rpi_picamera2_proxy()
    # print(rpi_picamera2_proxy)
    # exit()
    return Rpi_Picamera2(rpi_picamera2_proxy) 

class PiCamera2Plugin():

    name = 'pibooth_picamera2:camera'

    def __init__(self):
        pass
    
    # @pibooth.hookimpl
    # def pibooth_setup_camera(self):
    #     rpi_picamera2_proxy = get_rpi_picamera2_proxy()
    #     # print(rpi_picamera2_proxy)
    #     # exit()
    #     return Rpi_Picamera2(rpi_picamera2_proxy)
    