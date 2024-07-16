try:
    import pibooth
except Exception as e:
    print(e)
    exit()
from rpi_picamera2 import Rpi_Picamera2, get_rpi_picamera2_proxy
from pibooth.utils import LOGGER


# Release version
__version__ = "1.0.0"

@pibooth.hookimpl 
def pibooth_configure(cfg):
    """Declare new configuration options.
    """
    cfg.add_option('CAMERA','use_picamera2',1,
                    "Boolean value to use Picamera2 library and the new raspberry pi camera v3")

# This hook returns the custom camera proxy.
# It is defined here because yield statement in a hookwrapper with a 
# similar name is used to invoke it later. But check first if other cameras
# are installed or if the user specifically asks for this
@pibooth.hookimpl
def pibooth_setup_camera(cfg):
    
    rpi_picamera2_proxy = None
    if cfg.get('CAMERA','use_picamera2'):
        rpi_picamera2_proxy = get_rpi_picamera2_proxy()
    
    if not rpi_picamera2_proxy:
        LOGGER.info('Could not find picamera2')
        return
    return Rpi_Picamera2(rpi_picamera2_proxy) 


    
    