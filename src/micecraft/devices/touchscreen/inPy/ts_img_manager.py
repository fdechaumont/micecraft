from enum import Enum
from pathlib import Path

UNICODE_REPRESENTATION: dict[int, str | None] = {
    0: None,  # ERROR
    1: "",  # DARK
    2: "",  # LIGHT
    3: "\u2708",  # PLANE
    4: "\u273f",  # FLOWER
    5: "\u25b2",  # TRIANGLE
    6: "\u2666",  # LOSANGE
    7: "\u25cf",  # CIRCLE
    8: "\u2605",  # STAR
    9: None,  # TANGRAM
    10: None,  # DOOR
    11: None,  # SPIDER
    12: None,  # APPLE
    13: "\u273a",  # MAPPLE -> decorative
    14: None,  # BLOOM
    15: None,  # BOMB
    16: "\u03b2",  # BUG -> greek beta as placeholder
    17: "\u25ef",  # CIRCLES
    18: "4\u25cb",  # CIRCLES4
    19: "\u2716",  # X
    20: "\u2571",  # STRIPES_RECT_SW-NE
    21: "\u2572",  # STRIPES_RECT_NW-SE
    22: "\u2550",  # STRIPES_RECT_W-E
    23: "\u2551",  # STRIPES_RECT_N-S
    24: "\u2550",  # STRIPES_E-W
    25: "\u2572",  # STRIPES_NW-SE
    26: "\u2571",  # STRIPES_SW-NE
    27: "\u2551",  # STRIPES_N-S
    28: "\u25c9",  # STRIPES_CIRCLE
    29: "\u2714",  # TRUE
    30: "\u2717",  # FALSE
}


class TSImage(Enum):
    """Object representing every possible image that can be displayed on the
    touchscreen."""

    ERROR = 0
    DARK = 1
    LIGHT = 2
    PLANE = 3
    FLOWER = 4
    TRIANGLE = 5
    LOSANGE = 6
    CIRCLE = 7
    STAR = 8
    TANGRAM = 9
    DOOR = 10
    SPIDER = 11
    APPLE = 12
    MAPPLE = 13
    BLOOM = 14
    BOMB = 15
    BUG = 16
    CIRCLES = 17
    CIRCLES4 = 18
    X = 19
    STRIPES_RECT_SW_NE = 20
    STRIPES_RECT_NW_SE = 21
    STRIPES_RECT_W_E = 22
    STRIPES_RECT_N_S = 23
    STRIPES_E_W = 24
    STRIPES_NW_SE = 25
    STRIPES_SW_NE = 26
    STRIPES_N_S = 27
    STRIPES_CIRCLE = 28
    TRUE = 29
    FALSE = 30

    @staticmethod
    def get_images_path() -> dict[int, Path]:
        """Get a dictionary of all touchscreen image paths with their index as
        key."""
        img_folder = Path(__file__).parent
        sfx = [".png", ".jpg", ".jpeg"]
        list_paths = {}
        for filepath in img_folder.iterdir():
            if filepath.suffix not in sfx:
                continue
            id = int(filepath.name.split("_", 1)[0])
            list_paths[id] = filepath

        return list_paths

    def __str__(self) -> str:
        """Return the name of the TSImage."""
        return self.name

    def get_unicode(self):
        """Get the unicode representation of the TSImage or its name if no
        unicode is available."""
        txt = UNICODE_REPRESENTATION[self.value]
        if txt is None:
            return self.name
        return txt

    @staticmethod
    def get_name_from_id(id: int) -> str:
        """Get the name of the TSImage from its id or "UNKNOWN" if the id is
        invalid."""
        try:
            return TSImage(id).name
        except ValueError:
            return "UNKNOWN"

    @staticmethod
    def get_unicode_from_id(id: int) -> str:
        """Get the unicode representation of the TSImage or its name if no
        unicode is available or "UNKNOWN" if the id is invalid."""
        txt = UNICODE_REPRESENTATION.get(id)
        if txt is None:
            txt = TSImage.get_name_from_id(id)
        return txt

    def get_opposite(self):
        """Get the opposite TSImage."""
        opposites = {
            TSImage.DARK: TSImage.LIGHT,
            TSImage.LIGHT: TSImage.DARK,
            TSImage.FLOWER: TSImage.PLANE,
            TSImage.PLANE: TSImage.FLOWER,
            TSImage.TRUE: TSImage.FALSE,
            TSImage.FALSE: TSImage.TRUE,
        }
        if self not in opposites:
            return TSImage.ERROR

        return opposites[self]
