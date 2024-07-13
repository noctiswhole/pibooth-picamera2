import picamera2
import pygame
import time
import threading
try:
    import pibooth 
except Exception as ex:
    print(ex)
    exit()
from pibooth.utils import LOGGER
from pibooth.camera.rpi import RpiCamera
from picamera2 import Picamera2, Preview
from libcamera import Transform
from io import BytesIO
# cam = Picamera2()
# cam_config = cam.create_preview_configuration()
# cam.configure(cam_config)
# cam.start_preview(Preview.QTGL)
# cam.start()

def get_rpi_picamera2_proxy():
    
    cam = Picamera2()
    if cam:
        LOGGER.info('Use Picamera2 library')
        return cam
    return None

class Rpi_Picamera2(RpiCamera):

    """Plugin to manage the raspberry pi module v3
    """
    # Maximum resolution of the camera v3 module

    MAX_RESOLUTION = (4608,2592)

    def __init__(self, camera_proxy):
        super().__init__(camera_proxy)
        self.thread = None
        self.event = threading.Event()
        self.timeout = 0
        
    def _specific_initialization(self):
        """Camera initialization.
        """
        # Create capture configuration
    
    def _show_overlay(self, text, alpha):
        """Add an image as an overlay
        """
        if self._window:
            # return a rect the size of the preview window
            rect = self.get_rect(self.MAX_RESOLUTION)

            # Create an image padded to the required size
            size = (((rect.width + 31) // 32) * 32, ((rect.height + 15) // 16) * 16)

            # return a pil image with timeout on it
            image = self.build_overlay(size, str(text), alpha)

            # convert pil image to pygame.Surface
            self._overlay = pygame.image.frombuffer(image.tobytes(),size,'RGBA')
            
    def _hide_overlay(self):
        """"""
        if self._overlay:
            self._overlay = None

    def preview(self, window, flip=True):
        if self._cam._preview:
            # Preview is still running
            return
        # create rect dimensions for preview window
        self._window = window
        rect = self.get_rect(self.MAX_RESOLUTION)
        # Create preview configuration
        preview_config = self._cam.create_preview_configuration(main={'size':(rect.width,rect.height)})
        self._cam.configure(preview_config)
        
        # if the camera image has been flipped don't flip a second time
        # if flip:
        #     flip = 0
        # else:
            # flip = 1
        
        self._cam.start()
        # Starting camera withouth passing a preview window assing picamera2.previews.null_preview.NullPreview
        # set as daemon so that the program cleanly closes python program
        
        self.thread=threading.Thread(target=self.start_preview, daemon=True, 
                    args=(rect,))
        self.thread.start()
        

    def preview_countdown(self, timeout, alpha=60):
        """Show a countdown of 'timeout' seconds on the preview.
        Returns when the countdown is finished.
        Uses the same implementation as the parent but changes preview to _preview
        because of the difference between picamera and picamera2.
        """
        timeout = int(timeout)
        if timeout < 1:
            raise ValueError('Start time shall be greater than 0')
        if not self._cam._preview:
            raise RuntimeError('Preview shall be started first')
        # Use this condition to start preview loop in start preview
        self.timeout = timeout
        while timeout > 0:
            self._show_overlay(timeout, alpha)
            time.sleep(1)
            timeout -= 1
            self._hide_overlay()
            pygame.display.update()

    def start_preview(self, rect):
        """Target function to be run in a different thread"""
        while self.timeout > 0:
            array = self._cam.capture_array('main')
            
            # RGBX is 32 bit and has an unused 8 bit channel described as X
            # XBGR is used in the preview configuration
            pg_image = pygame.image.frombuffer(array.data, 
                        (rect.width, rect.height), 'RGBX')

            screen_rect = self._window.surface.get_rect()
            self._window.surface.blit(pg_image,
                                    pg_image.get_rect(center=screen_rect.center))
            if self._overlay:
                print(time.time(), ': ', self._overlay)
                self._window.surface.blit(self._overlay, self._overlay.get_rect(center=screen_rect.center))

    def stop_preview(self):
        if self._cam._preview:
            # Use method implemented in the parent class
            super().stop_preview()
            LOGGER.info('Sopped preview')
            
    def capture(self, effect=None):
        """Capture a new picture in a file.
        """
        stream = BytesIO()
        self._cam.capture_file(stream, format='jpeg')

        self._captures.append(stream)
        # Stop camera before next preview
        self._cam.stop()

    def quit(self):
        """Close camera
        """
        self._cam.close()

    

class PreviewWindow():
    def __init__(self, x, y, width, height):
        """Create a preview window based on the pygame sprite
        """
        self.x = x 
        self.y = y
        self.width = width 
        self.height = height 

    def update(self):
        """
        """
    def draw(self, screen):
        """
        """
        screen.blit(img, (x, y))