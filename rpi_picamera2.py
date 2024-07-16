import picamera2
import pygame
import time
import cv2
try:
    import pibooth 
except Exception as ex:
    print(ex)
    exit()
from pibooth.utils import LOGGER
from pibooth.camera.rpi import RpiCamera
from pibooth.language import get_translated_text
from picamera2 import Picamera2, Preview
from libcamera import Transform
from io import BytesIO
from PIL import Image

def get_rpi_picamera2_proxy():
    
    cam = Picamera2()
    if cam:
        LOGGER.info('Use Picamera2 library')
        return cam
    return None

class Rpi_Picamera2(RpiCamera):

    """Raspberry pi module v3 camera management
    """
    # Maximum resolution of the camera v3 module
    MAX_RESOLUTION = (4608,2592)
    IMAGE_EFFECTS = [u'none',
                     u'blur',
                     u'contour',
                     u'detail',
                     u'edge_enhance',
                     u'edge_enhance_more',
                     u'emboss',
                     u'find_edges',
                     u'smooth',
                     u'smooth_more',
                     u'sharpen']

    def __init__(self, camera_proxy):
        super().__init__(camera_proxy)
        self._preview_config = None
        self._capture_config = None
        
    def _specific_initialization(self):
        """Camera initialization.
        """
        resolution = self._transform()
        # Create preview configuration
        self._preview_config = self._cam.create_preview_configuration(main={'size':resolution}, 
                                transform=Transform(hflip=self.preview_flip))
        self._capture_config = self._cam.create_still_configuration(main={'size':resolution},
                                transform=Transform(hflip=self.capture_flip))
        
    
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
            self.update_preview()

    def _hide_overlay(self):
        """"""
        if self._overlay:
            self._overlay = None
            self.update_preview()

    def _transform(self):
        """Return tuple for configuring picamera"""
        if self.preview_rotation in (90,270):
            return self.resolution[1], self.resolution[0]
        else:
            return self.resolution
    
    def _rotate_image(self, image, rotation):
        """Rotate image clockwise"""
        return pygame.transform.rotate(image,360-rotation) if rotation != 0 else image

    def get_rect(self, max_size):
        if self.preview_rotation in (90,270):
            rect = super().get_rect(max_size)
            rect.width, rect.height = rect.height, rect.width 
            return rect
        return super().get_rect(max_size) 

    def preview(self, window, flip=True):
        if self._cam._preview:
            # Preview is still running
            return
        # create rect dimensions for preview window
        self._window = window
        
        # if the camera image has been flipped don't flip a second time
        # The flip overrides any previous flip value
        if self.preview_flip != flip:
            self.preview_flip = flip
            # if rotation is 90 or 270 degrees, vertically flip the image
            if self.preview_rotation in (90,270):
                self._preview_config['transform'].vflip = flip
            else:
                self._preview_config['transform'].hflip = flip

        self._cam.configure(self._preview_config)
        self._cam.start()
        self.update_preview()

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
        time_stamp = time.time() 
        
        while timeout > 0:
            self._show_overlay(timeout, alpha)
            if time.time()-time_stamp > 1:
                timeout -= 1
                time_stamp = time.time()
                self._hide_overlay()
        # Keep smile for 1 second
        while time.time()-time_stamp < 1:
            self._show_overlay(get_translated_text('smile'), alpha)
        # Remove smile
        # _hide_overlay sets self._overlay = None otherwise app stalls after capture method is called
        self._hide_overlay()

    def preview_wait(self, timeout, alpha=60):
        time_stamp = time.time()
        # Keep preview for the duration of timeout
        while time.time() - time_stamp < timeout:
            self.update_preview()
        time_stamp = time.time()
        # Keep smile for 1 second
        while time.time()-time_stamp < 1:
            self._show_overlay(get_translated_text('smile'), alpha)
        self._hide_overlay()

    def update_preview(self):
        """Capture image and update screen with image"""
        array = self._cam.capture_array('main')
        rect = self.get_rect(self.MAX_RESOLUTION)
        # Resize high resolution image to fit smaller window
        res = cv2.resize(array, dsize=(rect.width,rect.height), 
                interpolation=cv2.INTER_CUBIC)
        # RGBX is 32 bit and has an unused 8 bit channel described as X
        # XBGR is used in the preview configuration
        pg_image = pygame.image.frombuffer(res.data, 
                    (rect.width, rect.height), 'RGBX')
        pg_image = self._rotate_image(pg_image, self.preview_rotation)
        screen_rect = self._window.surface.get_rect()
        self._window.surface.blit(pg_image,
                                pg_image.get_rect(center=screen_rect.center))
        if self._overlay:
            self._window.surface.blit(self._overlay, self._overlay.get_rect(center=screen_rect.center))
        pygame.display.update() 

    def stop_preview(self):
        if self._cam._preview:
            # Use method implemented in the parent class
            super().stop_preview()
            LOGGER.info('Sopped preview')
            
    def capture(self, effect=None):
        """Capture a new picture in a file.
        """
        effect = str(effect).lower()
        if effect not in self.IMAGE_EFFECTS:
            LOGGER.info(f'{effect} not in capture effects')
        if effect != 'none' and effect in self.IMAGE_EFFECTS:
            LOGGER.info(f'{self.__class__.__name__} has not been implemented with any effects')

        stream = BytesIO()
        self._cam.switch_mode(self._capture_config)
        self._cam.capture_file(stream, format='jpeg')
        self._captures.append(stream)
        # Reconfigure and Stop camera before next preview
        self._cam.switch_mode(self._preview_config)
        self._cam.stop()
       

    def quit(self):
        """Close camera
        """
        self._cam.close()

    

