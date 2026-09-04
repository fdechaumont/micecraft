import pygame
import serial
import os
from time import sleep
from enum import Enum
import traceback
import math


class TouchScreen:

    class Mode(Enum):
        FULLSCREEN = 1
        MOUSE = 2
        RAT = 3

    def __init__(self):

        print("Starting TouchScreen")

        print("Starting serial...")
        self.ser = serial.Serial(
            "/dev/ttyS0", baudrate=115200, write_timeout=2, timeout=0
        )  # 115200
        # ,parity=serial.PARITY_ODD,stopbits = serial.STOPBITS_TWO,bytesize= serial.SEVENBITS

        print(self.ser.name)
        self.send("Starting touchscreen...")

        self.lastError = ""

        pygame.init()

        self.gameDisplay = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        pygame.display.set_caption("MiceCraft Touchscreen")

        self.transparency = 255

        self.display_width = self.gameDisplay.get_width()
        self.display_height = self.gameDisplay.get_height()
        print(f"Screen size: {self.display_width}x{self.display_height}")

        self.yOffset = 0
        self.bg: pygame.Surface | None = None
        """None for black background, display the image otherwise."""
        self.screen_diag = 1 + int(
            math.hypot(self.display_width, self.display_height)
        )

        self.mode = self.Mode.FULLSCREEN
        self.inputBuffer = ""
        pygame.mouse.set_visible(False)

        self.black = (0, 0, 0)
        self.white = (255, 255, 255)

        self.clock = pygame.time.Clock()

        self.img_size = int(self.display_width / 3.5)
        self.img_displayed: dict[str, pygame.Surface] = {}
        """name: pygame.Surface"""

        self.images = []
        self.fingers = {}

        self.running = True
        self.send("Touchscreen started")

    def setShowCalibration(self, enabled: bool):
        self.show_calibration = enabled

    def loadImage(self, file):
        img = pygame.image.load(file)
        img = pygame.transform.scale(img, (self.img_size, self.img_size))
        img = img.convert_alpha()

        img.fill(
            (255, 255, 255, self.transparency),
            special_flags=pygame.BLEND_RGBA_MULT,
        )
        return img

    def loadImages(self, files):
        self.files = files
        self.reloadImages()

    def reloadImages(self):
        """Reload images.

        New behaviour: `self.images` is a dict. If a filename follows the
        pattern "xxx_name.ext" the key will be "xxx". Otherwise numeric
        integer keys are used for compatibility. The stored value is a
        tuple `(surface, file)` to remain compatible with existing code.
        """
        self.images = {}
        i = 0
        for file in self.files:
            surf = self.loadImage(file)
            base = os.path.basename(file)
            name, _ext = os.path.splitext(base)
            if "_" in name:
                key = name.split("_", 1)[0]
                # later files override earlier ones for the same key
                self.images[key] = (surf, file)
            else:
                self.images[i] = (surf, file)
                i += 1

    def getImage(self, index):
        # Accept either a dict key (string) or an integer index for
        # backward compatibility.
        try:
            entry = self.images[index]
        except Exception:
            # try positional index into the dict values
            try:
                idx = int(index)
                entry = list(self.images.values())[idx]
            except Exception:
                self.sendErrorFeedBack(f"getImage: Image key error:{index}")
                try:
                    entry = list(self.images.values())[0]
                except Exception:
                    return None
        return entry[0]

    def createStripesImage(
        self, white_height: int, black_height: int, angle: float
    ) -> pygame.Surface:

        stripe_height = max(0, int(white_height)) + max(0, int(black_height))
        if stripe_height <= 0:
            return pygame.Surface(
                (self.img_size, self.img_size), flags=pygame.SRCALPHA
            )

        img_diag = (
            int(math.ceil(math.hypot(self.img_size, self.img_size)))
            + stripe_height
        )
        surf = pygame.Surface((img_diag, img_diag), flags=pygame.SRCALPHA)

        white_h = max(0, int(white_height))
        black_h = max(0, int(black_height))
        for y in range(0, img_diag, stripe_height):
            if white_h > 0:
                pygame.draw.rect(surf, self.white, (0, y, img_diag, white_h))
            if black_h > 0:
                pygame.draw.rect(
                    surf, self.black, (0, y + white_h, img_diag, black_h)
                )

        rotated = pygame.transform.rotate(surf, angle % 180)

        rx = rotated.get_width() // 2 - self.img_size // 2
        ry = rotated.get_height() // 2 - self.img_size // 2
        crop_rect = pygame.Rect(rx, ry, self.img_size, self.img_size)
        crop_rect.clamp_ip(rotated.get_rect())
        final = rotated.subsurface(crop_rect).copy()
        return final

    def showImage(self, imageIndex, x, y):
        x = int(self.getXCenter(x) - self.img_size / 2)
        y = int(self.getYCenter(y) - self.img_size / 2)
        self.gameDisplay.blit(self.getImage(imageIndex), (x, y))

    def showXYImage(self, name):
        image = self.img_displayed[name]
        imageIndex = image[0]
        x = image[1]
        y = image[2]
        r = image[3]
        s = image[4]

        size = self.img_size * s

        # center image
        # x = int ( x - size/2 )
        # y = int ( y - size/2 )

        i2 = pygame.transform.rotozoom(self.getImage(imageIndex), r, s)

        x = int(x - i2.get_width() / 2)
        y = int(y - i2.get_height() / 2)

        self.gameDisplay.blit(i2, (x, y))

    def showXYStripesImage(self, name: str):
        surf, x, y = self.currentStripesImages[name]

        x = x - surf.get_width() // 2
        y = y - surf.get_height() // 2
        self.gameDisplay.blit(surf, (x, y))

    def setImage(self, imageIndex, x, y=1):
        self.currentImages[(x, y)] = imageIndex

    def removeImage(self, x, y=1):
        if ((x, y)) in self.currentImages:
            self.currentImages.pop((x, y))

    def setXYImage(self, name, index, x, y, r, s):
        self.img_displayed[name] = [index, x, y, r, s]

    def removeXYImage(self, name):
        if name in self.img_displayed:
            self.img_displayed.pop(name)

    def setXYStripesImage(
        self,
        name: str,
        white_height: int,
        black_height: int,
        angle: float,
        x: int,
        y: int,
    ):
        surf = self.createStripesImage(white_height, black_height, angle)
        self.currentStripesImages[name] = (surf, x, y)

    def removeXYStripesImage(self, name: str):
        if name in self.currentStripesImages:
            self.currentStripesImages.pop(name)

    def removeAllImages(self):
        self.currentImages = {}
        self.img_displayed = {}
        self.currentStripesImages = {}

    def getXCenter(self, x):
        w = self.display_width / self.nbCols
        return int((x - 1) * (w) + w / 2)

    def getYCenter(self, y):
        h = self.display_height / self.nbRows
        return int((y - 1) * (h) + h / 2 + self.yOffset)

    def drawCalibration(self):
        for x in range(1, self.nbCols + 1):
            x = self.getXCenter(x)
            pygame.draw.line(
                self.gameDisplay,
                (255, 0, 0),
                (x, 0),
                (x, self.display_height),
                5,
            )
        for y in range(1, self.nbRows + 1):
            y = self.getYCenter(y)
            pygame.draw.line(
                self.gameDisplay,
                (255, 0, 0),
                (0, y),
                (self.display_width, y),
                5,
            )

    def setBgStripes(self, white_height: int, black_height: int, angle: float):
        """Configure full-screen white/black stripe pattern.

        Parameters:
        -----------
        white_height: int - height of white stripes in pixels (0 for no white stripes)
        black_height: int - height of black stripes in pixels (0 for no black stripes)
        angle: float - rotation angle of stripes in degrees (-90 to 90)

        Example usage:
        --------------
        ts.setStripes(white_height=20, black_height=20, angle=45)

        This would create a pattern of 20px white stripes alternating with
        20px black stripes, rotated 45 degrees.
        """

        # Precompute a fullscreen Surface containing the rotated stripes
        self.bg = self.create_bg_stripes_surface(
            max(0, white_height), max(0, black_height), angle % 180
        )

    def create_bg_stripes_surface(
        self, white_height: int, black_height: int, angle: float
    ) -> pygame.Surface:
        """Create a Surface sized to the display containing rotated stripes.

        Returns a Surface exactly `display_width` x `display_height` ready
        to blit as a background.
        """
        stripe_height = white_height + black_height
        if stripe_height <= 0:
            surf = pygame.Surface((self.display_width, self.display_height))
            surf.fill(self.black)
            return surf

        # create a square large enough to cover the rotated area
        diag = int(
            math.ceil(math.hypot(self.display_width, self.display_height))
        )
        img_size = diag + stripe_height
        temp = pygame.Surface((img_size, img_size), flags=pygame.SRCALPHA)

        for y in range(0, img_size, stripe_height):
            if white_height > 0:
                pygame.draw.rect(
                    temp, self.white, (0, y, img_size, white_height)
                )
            if black_height > 0:
                pygame.draw.rect(
                    temp,
                    self.black,
                    (0, y + white_height, img_size, black_height),
                )

        rotated = pygame.transform.rotate(temp, angle % 180)

        rx = rotated.get_width() // 2 - self.display_width // 2
        ry = rotated.get_height() // 2 - self.display_height // 2
        crop_rect = pygame.Rect(
            rx, ry, self.display_width, self.display_height
        )
        crop_rect.clamp_ip(rotated.get_rect())
        final = rotated.subsurface(crop_rect).copy()
        return final

    def removeBg(self):
        """Remove any stripe pattern and return to normal display."""
        self.bg = None

    def _draw_bg(self):
        """Draw alternating white/black stripes filling the screen, rotated by angle."""
        if self.bg is None:
            self.gameDisplay.fill(self.black)
            return

        # `self.bg` is a precomputed Surface matching the display size
        try:
            self.gameDisplay.blit(self.bg, (0, 0))
        except Exception:
            # defensive fallback to solid black if bg is invalid
            self.gameDisplay.fill(self.black)

    def fingerDown(self, xf, yf):
        # test if the symbol is touched

        touched = False

        for name in self.img_displayed:
            image = self.img_displayed[name]
            imageIndex = image[0]
            x = image[1]
            y = image[2]
            r = image[3]
            s = image[4]
            size = self.img_size * s
            print("xy test touch", size, x, y, xf, yf)
            dist = math.dist((x, y), (xf, yf))
            print("dist: ", dist, dist < size / 2)
            if dist < size / 2:
                self.send(
                    f"symbol xy touched {name} id {imageIndex} at {x},{y},{int(xf)},{int(yf)}"
                )
                touched = True

        for coord, imageIndex in self.currentImages.items():
            x = coord[0]
            y = coord[1]
            x1 = int(self.getXCenter(x) - self.img_size / 2)
            y1 = int(self.getYCenter(y) - self.img_size / 2)
            x2 = x1 + self.img_size
            y2 = y1 + self.img_size
            if xf > x1 and xf < x2 and yf > y1 and yf < y2:
                # touched
                self.send(
                    f"symbol touched id {imageIndex} at {x},{y},{int(xf)},{int(yf)}"
                )
                touched = True

        if not touched:
            self.send(f"missed {int(xf)},{int(yf)}")

    def send(self, message):
        message += "\n"
        message = message.encode("utf-8")
        self.ser.write(message)

    def processCommands(self):

        dataIn = self.ser.readline()

        try:
            dataIn = dataIn.decode("utf_8")
        except:
            # error in decode
            self.sendErrorFeedBack("Can't uf8-decode command")
            return

        self.inputBuffer += dataIn
        # print( f"input buffer: {self.inputBuffer}")

        command = None

        buffer = self.inputBuffer

        if "\n" in buffer:
            splits = buffer.split("\n")
            command = splits[0]

            loc = buffer.index("\n")

            """
            print("---" )
            print( f"slash n location: {loc} ")
            print( f"Input buffer : {self.inputBuffer}" )
            print( f"Splits : {splits}")
            print( f"Command : {command}")
            """

            self.inputBuffer = self.inputBuffer[len(command) + 1 :]

        """
        if "\n" in self.inputBuffer:
            splits = self.inputBuffer.split("\n")
            command = splits[0]
            
            loc = self.inputBuffer.index("\n")
            print("---" )
            print( f"slash n location: {loc} ")
            print( f"Input buffer : {self.inputBuffer}" )
            print( f"Splits : {splits}")
            print( f"Command : {command}")
            
            self.inputBuffer = self.inputBuffer[ len(command)+1 : ]
        """

        if command != None:
            if len(command) > 0:
                print(f"process command : {command}")

                c = command.split(" ")

                if "hello" in c[0]:
                    self.send("Touchscreen - driver v2.2")

                if "setImage" in c[0]:
                    # setImage 0 1 1
                    # print( "current command:" + command )

                    imageIndex = int(c[1])
                    x = int(c[2])
                    y = int(c[3])
                    self.setImage(imageIndex, x, y)

                if "setXYImage" in c[0]:

                    print(f"setXYcommand: {command}")

                    name = c[1]
                    imageIndex = int(c[2])
                    x = float(c[3])
                    y = float(c[4])
                    r = float(c[5])
                    s = float(c[6])
                    self.setXYImage(name, imageIndex, x, y, r, s)

                if "removeXYImage" in c[0]:
                    name = c[1]
                    ts.removeXYImage(name)

                if "removeImage" in c[0]:

                    x = int(c[1])
                    y = int(c[2])
                    ts.removeImage(x, y)

                if "config" in c[0]:
                    # config col row size

                    x = int(c[1])
                    y = int(c[2])
                    size = int(c[3])
                    self.nbCols = x
                    self.nbRows = y
                    self.img_size = size
                    self.reloadImages()

                if "transparency" in c[0]:
                    # from 0 to 255

                    self.transparency = int(c[1])
                    self.reloadImages()

                if "yOffset" in c[0]:

                    self.yOffset = int(c[1])

                # todo: collaspe all the mode in one variable
                if "mouseMode" in c[0]:
                    self.mode = self.Mode.MOUSE

                if "ratMode" in c[0]:
                    self.mode = self.Mode.RAT

                if "normalMode" in c[0]:
                    self.mode = self.Mode.NORMAL

                if "ping" in c[0]:

                    self.send("pong")

                if "clear" in c[0]:
                    self.removeAllImages()
                    self.removeBg()

                if "calibration" in c[0]:
                    if "show" in command:
                        self.show_calibration = True
                    if "hide" in command:
                        self.show_calibration = False

                if "crash" in c[0]:
                    raise Exception("Crash asked by user")

                if "setBgStripes" in c[0]:
                    white = int(c[1])
                    black = int(c[2])
                    angle = float(c[3])
                    self.setBgStripes(white, black, angle)

                if "removeBg" in c[0]:
                    self.removeBg()

                if "setXYStripesImage" in c[0]:
                    name = c[1]
                    white = int(c[2])
                    black = int(c[3])
                    angle = float(c[4])
                    x = int(c[5])
                    y = int(c[6])
                    self.setXYStripesImage(name, white, black, angle, x, y)

                if "removeXYStripesImage" in c[0]:
                    name = c[1]
                    self.removeXYStripesImage(name)

        return command

    def sendErrorFeedBack(self, error):
        if (
            self.lastError == error
        ):  # check error to avoid repeating the same one all the time
            return

        self.send(f"Touchscreen - error - traceback: {error}")
        self.lastError = error

    def process(self):

        for i in range(10):
            command = self.processCommands()
            if command == None:
                break

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_q:
                    self.running = False
                    print("Q key hit: exit")
                if event.key == pygame.K_c:
                    self.show_calibration = not self.show_calibration
            if event.type == pygame.MOUSEBUTTONDOWN:
                print("Mouse button pressed")

            if event.type == pygame.FINGERDOWN:
                # self.send( f"debug area size: {self.gameDisplay.get_height()},{self.gameDisplay.get_width()}")
                # self.send( f"debug event.x,y : {event.x},{event.y}")

                # coordinates from 0 to 1
                xx = event.x
                yy = event.y

                if self.mode == self.Mode.RAT:
                    # print("rat mode")

                    # in rat mode, the screen is reversed, meaning the screen is in
                    # landscape layout and the wire is getting out from the top left corner when
                    # the user watch the screen.
                    ratioY = 0.32  # the ratio of the y part of the screen to be used.
                    yy = ((1 - event.y) - ratioY) * (1 / (1 - ratioY))
                    xx = 1 - event.x

                if self.mode == self.Mode.MOUSE:
                    # rotate

                    # yy = (1-(event.x+0.5))*2 # translate up

                    # transform

                    """
                    # bottom of the screen
                    yy = (1-(event.x+0.6))*2.5
                    xx = event.y*1.05
                    """
                    yy = (1 - (event.x + 0.25)) * 2.5
                    xx = event.y * 1.05

                    """
                    xx = (1-(xx+0.5))*2 # translate up
                    xxx = yy
                    yyy = xx
                    xx = xxx
                    yy = yyy
                    """

                x = xx * self.gameDisplay.get_width()
                y = yy * self.gameDisplay.get_height()

                self.fingers[event.finger_id] = x, y
                print("finger down", event.finger_id, x, y)
                self.fingerDown(x, y)

            if event.type == pygame.FINGERUP:
                self.fingers.pop(event.finger_id, None)
                print("finger up", event.finger_id)

        self._draw_bg()

        for coord, imageIndex in self.currentImages.items():
            x = coord[0]
            y = coord[1]
            self.showImage(imageIndex, x, y)

        for image in self.img_displayed:
            self.showXYImage(image)

        for name in self.currentStripesImages:
            self.showXYStripesImage(name)

        """
        ts.showImage( 1, 2, 1 )
        ts.showImage( 2, 3, 1 )
        """

        if self.show_calibration:
            self.drawCalibration()

            for finger in self.fingers:
                xf, yf = self.fingers[finger]
                pygame.draw.line(
                    self.gameDisplay,
                    (0, 255, 0),
                    (xf - 50, yf - 50),
                    (xf + 50, yf + 50),
                    5,
                )
                pygame.draw.line(
                    self.gameDisplay,
                    (0, 255, 0),
                    (xf + 50, yf - 50),
                    (xf - 50, yf + 50),
                    5,
                )
        pygame.display.update()
        self.clock.tick(30)


if __name__ == "__main__":

    print("Starting touchscreen inner example...")

    abspath = os.path.abspath(__file__)
    dname = os.path.dirname(abspath)
    os.chdir(dname)

    """
    #ser = serial.Serial("/dev/ttyS0",baudrate=9600, writeTimeout=2, timeout=10 ,parity=serial.PARITY_NONE, stopbits = serial.STOPBITS_ONE, bytesize = serial.EIGHTBITS )
    ser = serial.Serial("/dev/ttyS0",baudrate=115200, writeTimeout=2, timeout=10 )
    print( ser.name )
    #while True :
    
    i=0
    while True:
        ser.flush()
        i+=1
        print( i, "flushin")
        #c=c+"echo\n"
        try:
            ser.write( "hello heloow\n".encode("utf_8" ) )
            print("writeok")
        except:
            print("timeout")
    ser.close()
    quit()
    """
    ts = TouchScreen()
    ts.loadImages(
        [
            "003_plane.png",  # "plane.jpg",
            "004_flower.png",  # "flower.jpg",
            "015_bomb.png",  # "bomb.jpg",
            "011_spider.jpg",  # "spider.jpg",
            "020_stripes_rect_SW-NE.jpg",  # "001.jpg",
            "021_stripes_rect_NW-SE.jpg",  # "003.jpg",
            "028_stripes_circle.jpg",  # "004.jpg",
            "002_white.png",  # "005.jpg",
            "001_black.png",  # "006.jpg",
            "022_stripes_rect_W-E.jpg",  # "007.jpg",
            "013_mapple.jpg",  # "008.jpg",
            "023_stripes_rect_N-S.jpg",  # "009.jpg",
            "016_bug.png",  # "bug.png",
        ]
    )
    ts.setShowCalibration(True)

    ts.setImage(0, 1, 1)
    ts.setImage(1, 2, 1)
    ts.setImage(2, 3, 1)

    # ts.setXYImage( "testXYImage", 12, 1920/2,1080/2,45,0.5 )

    # ts.removeImage( 1 , 1 )

    while ts.running:

        try:
            ts.process()
        except Exception as e:

            error = traceback.format_exc()
            print(error)
            ts.running = False

        """
        try:
            ts.process()
        except Exception as e:
            
            error = traceback.format_exc()
            error = error.replace("\n","*")
            ts.sendErrorFeedBack( f"{error}" )
        """

        sleep(0.001)

    pygame.quit()
    print("Quit")
    quit()
