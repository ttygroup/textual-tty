"""
Color handling for the terminal emulator.

This module is responsible for parsing color strings and managing the dynamic
256-color palette that legacy terminal applications can modify.

While the final display is handled by Textual, which has its own sophisticated
`Color` class, this module acts as a translation layer. It handles legacy
terminal color commands (like redefining palette entries or using X11 color
names) and converts them into the modern `textual.color.Color` objects that
the renderer expects.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Dict, Optional, Tuple
from textual.color import Color


# A dictionary to hold the mapping of X11 color names to their hex codes.
# This is necessary because tmux supports a wider range of names than standard
# CSS, and a high-fidelity emulator must recognize them. This dictionary will
# be populated with the extensive list from tmux's colour.c.
X11_NAMES = {
    "AliceBlue": "#f0f8ff",
    "AntiqueWhite": "#faebd7",
    "AntiqueWhite1": "#ffefdb",
    "AntiqueWhite2": "#eedfcc",
    "AntiqueWhite3": "#cdc0b0",
    "AntiqueWhite4": "#8b8378",
    "BlanchedAlmond": "#ffebcd",
    "BlueViolet": "#8a2be2",
    "CadetBlue": "#5f9ea0",
    "CadetBlue1": "#98f5ff",
    "CadetBlue2": "#8ee5ee",
    "CadetBlue3": "#7ac5cd",
    "CadetBlue4": "#53868b",
    "CornflowerBlue": "#6495ed",
    "DarkBlue": "#00008b",
    "DarkCyan": "#008b8b",
    "DarkGoldenrod": "#b8860b",
    "DarkGoldenrod1": "#ffb90f",
    "DarkGoldenrod2": "#eead0e",
    "DarkGoldenrod3": "#cd950c",
    "DarkGoldenrod4": "#8b6508",
    "DarkGray": "#a9a9a9",
    "DarkGreen": "#006400",
    "DarkGrey": "#a9a9a9",
    "DarkKhaki": "#bdb76b",
    "DarkMagenta": "#8b008b",
    "DarkOliveGreen": "#556b2f",
    "DarkOliveGreen1": "#caff70",
    "DarkOliveGreen2": "#bcee68",
    "DarkOliveGreen3": "#a2cd5a",
    "DarkOliveGreen4": "#6e8b3d",
    "DarkOrange": "#ff8c00",
    "DarkOrange1": "#ff7f00",
    "DarkOrange2": "#ee7600",
    "DarkOrange3": "#cd6600",
    "DarkOrange4": "#8b4500",
    "DarkOrchid": "#9932cc",
    "DarkOrchid1": "#bf3eff",
    "DarkOrchid2": "#b23aee",
    "DarkOrchid3": "#9a32cd",
    "DarkOrchid4": "#68228b",
    "DarkRed": "#8b0000",
    "DarkSalmon": "#e9967a",
    "DarkSeaGreen": "#8fbc8f",
    "DarkSeaGreen1": "#c1ffc1",
    "DarkSeaGreen2": "#b4eeb4",
    "DarkSeaGreen3": "#9bcd9b",
    "DarkSeaGreen4": "#698b69",
    "DarkSlateBlue": "#483d8b",
    "DarkSlateGray": "#2f4f4f",
    "DarkSlateGray1": "#97ffff",
    "DarkSlateGray2": "#8deeee",
    "DarkSlateGray3": "#79cdcd",
    "DarkSlateGray4": "#528b8b",
    "DarkSlateGrey": "#2f4f4f",
    "DarkTurquoise": "#00ced1",
    "DarkViolet": "#9400d3",
    "DeepPink": "#ff1493",
    "DeepPink1": "#ff1493",
    "DeepPink2": "#ee1289",
    "DeepPink3": "#cd1076",
    "DeepPink4": "#8b0a50",
    "DeepSkyBlue": "#00bfff",
    "DeepSkyBlue1": "#00bfff",
    "DeepSkyBlue2": "#00b2ee",
    "DeepSkyBlue3": "#009acd",
    "DeepSkyBlue4": "#00688b",
    "DimGray": "#696969",
    "DimGrey": "#696969",
    "DodgerBlue": "#1e90ff",
    "DodgerBlue1": "#1e90ff",
    "DodgerBlue2": "#1c86ee",
    "DodgerBlue3": "#1874cd",
    "DodgerBlue4": "#104e8b",
    "FloralWhite": "#fffaf0",
    "ForestGreen": "#228b22",
    "GhostWhite": "#f8f8ff",
    "GreenYellow": "#adff2f",
    "HotPink": "#ff69b4",
    "HotPink1": "#ff6eb4",
    "HotPink2": "#ee6aa7",
    "HotPink3": "#cd6090",
    "HotPink4": "#8b3a62",
    "IndianRed": "#cd5c5c",
    "IndianRed1": "#ff6a6a",
    "IndianRed2": "#ee6363",
    "IndianRed3": "#cd5555",
    "IndianRed4": "#8b3a3a",
    "LavenderBlush": "#fff0f5",
    "LavenderBlush1": "#fff0f5",
    "LavenderBlush2": "#eee0e5",
    "LavenderBlush3": "#cdc1c5",
    "LavenderBlush4": "#8b8386",
    "LawnGreen": "#7cfc00",
    "LemonChiffon": "#fffacd",
    "LemonChiffon1": "#fffacd",
    "LemonChiffon2": "#eee9bf",
    "LemonChiffon3": "#cdc9a5",
    "LemonChiffon4": "#8b8970",
    "LightBlue": "#add8e6",
    "LightBlue1": "#bfefff",
    "LightBlue2": "#b2dfee",
    "LightBlue3": "#9ac0cd",
    "LightBlue4": "#68838b",
    "LightCoral": "#f08080",
    "LightCyan": "#e0ffff",
    "LightCyan1": "#e0ffff",
    "LightCyan2": "#d1eeee",
    "LightCyan3": "#b4cdcd",
    "LightCyan4": "#7a8b8b",
    "LightGoldenrod": "#eedd82",
    "LightGoldenrod1": "#ffec8b",
    "LightGoldenrod2": "#eedc82",
    "LightGoldenrod3": "#cdbe70",
    "LightGoldenrod4": "#8b814c",
    "LightGoldenrodYellow": "#fafad2",
    "LightGray": "#d3d3d3",
    "LightGreen": "#90ee90",
    "LightGrey": "#d3d3d3",
    "LightPink": "#ffb6c1",
    "LightPink1": "#ffaeb9",
    "LightPink2": "#eea2ad",
    "LightPink3": "#cd8c95",
    "LightPink4": "#8b5f65",
    "LightSalmon": "#ffa07a",
    "LightSalmon1": "#ffa07a",
    "LightSalmon2": "#ee9572",
    "LightSalmon3": "#cd8162",
    "LightSalmon4": "#8b5742",
    "LightSeaGreen": "#20b2aa",
    "LightSkyBlue": "#87cefa",
    "LightSkyBlue1": "#b0e2ff",
    "LightSkyBlue2": "#a4d3ee",
    "LightSkyBlue3": "#8db6cd",
    "LightSkyBlue4": "#607b8b",
    "LightSlateBlue": "#8470ff",
    "LightSlateGray": "#778899",
    "LightSlateGrey": "#778899",
    "LightSteelBlue": "#b0c4de",
    "LightSteelBlue1": "#cae1ff",
    "LightSteelBlue2": "#bcd2ee",
    "LightSteelBlue3": "#a2b5cd",
    "LightSteelBlue4": "#6e7b8b",
    "LightYellow": "#ffffe0",
    "LightYellow1": "#ffffe0",
    "LightYellow2": "#eeeed1",
    "LightYellow3": "#cdcdb4",
    "LightYellow4": "#8b8b7a",
    "LimeGreen": "#32cd32",
    "MediumAquamarine": "#66cdaa",
    "MediumBlue": "#0000cd",
    "MediumOrchid": "#ba55d3",
    "MediumOrchid1": "#e066ff",
    "MediumOrchid2": "#d15fee",
    "MediumOrchid3": "#b452cd",
    "MediumOrchid4": "#7a378b",
    "MediumPurple": "#9370db",
    "MediumPurple1": "#ab82ff",
    "MediumPurple2": "#9f79ee",
    "MediumPurple3": "#8968cd",
    "MediumPurple4": "#5d478b",
    "MediumSeaGreen": "#3cb371",
    "MediumSlateBlue": "#7b68ee",
    "MediumSpringGreen": "#00fa9a",
    "MediumTurquoise": "#48d1cc",
    "MediumVioletRed": "#c71585",
    "MidnightBlue": "#191970",
    "MintCream": "#f5fffa",
    "MistyRose": "#ffe4e1",
    "MistyRose1": "#ffe4e1",
    "MistyRose2": "#eed5d2",
    "MistyRose3": "#cdb7b5",
    "MistyRose4": "#8b7d7b",
    "NavajoWhite": "#ffdead",
    "NavajoWhite1": "#ffdead",
    "NavajoWhite2": "#eecfa1",
    "NavajoWhite3": "#cdb38b",
    "NavajoWhite4": "#8b795e",
    "NavyBlue": "#000080",
    "OldLace": "#fdf5e6",
    "OliveDrab": "#6b8e23",
    "OliveDrab1": "#c0ff3e",
    "OliveDrab2": "#b3ee3a",
    "OliveDrab3": "#9acd32",
    "OliveDrab4": "#698b22",
    "OrangeRed": "#ff4500",
    "OrangeRed1": "#ff4500",
    "OrangeRed2": "#ee4000",
    "OrangeRed3": "#cd3700",
    "OrangeRed4": "#8b2500",
    "PaleGoldenrod": "#eee8aa",
    "PaleGreen": "#98fb98",
    "PaleGreen1": "#9aff9a",
    "PaleGreen2": "#90ee90",
    "PaleGreen3": "#7ccd7c",
    "PaleGreen4": "#548b54",
    "PaleTurquoise": "#afeeee",
    "PaleTurquoise1": "#bbffff",
    "PaleTurquoise2": "#aeeeee",
    "PaleTurquoise3": "#96cdcd",
    "PaleTurquoise4": "#668b8b",
    "PaleVioletRed": "#db7093",
    "PaleVioletRed1": "#ff82ab",
    "PaleVioletRed2": "#ee799f",
    "PaleVioletRed3": "#cd6889",
    "PaleVioletRed4": "#8b475d",
    "PapayaWhip": "#ffefd5",
    "PeachPuff": "#ffdab9",
    "PeachPuff1": "#ffdab9",
    "PeachPuff2": "#eecbad",
    "PeachPuff3": "#cdaf95",
    "PeachPuff4": "#8b7765",
    "PowderBlue": "#b0e0e6",
    "RebeccaPurple": "#663399",
    "RosyBrown": "#bc8f8f",
    "RosyBrown1": "#ffc1c1",
    "RosyBrown2": "#eeb4b4",
    "RosyBrown3": "#cd9b9b",
    "RosyBrown4": "#8b6969",
    "RoyalBlue": "#4169e1",
    "RoyalBlue1": "#4876ff",
    "RoyalBlue2": "#436eee",
    "RoyalBlue3": "#3a5fcd",
    "RoyalBlue4": "#27408b",
    "SaddleBrown": "#8b4513",
    "SandyBrown": "#f4a460",
    "SeaGreen": "#2e8b57",
    "SeaGreen1": "#54ff9f",
    "SeaGreen2": "#4eee94",
    "SeaGreen3": "#43cd80",
    "SeaGreen4": "#2e8b57",
    "SkyBlue": "#87ceeb",
    "SkyBlue1": "#87ceff",
    "SkyBlue2": "#7ec0ee",
    "SkyBlue3": "#6ca6cd",
    "SkyBlue4": "#4a708b",
    "SlateBlue": "#6a5acd",
    "SlateBlue1": "#836fff",
    "SlateBlue2": "#7a67ee",
    "SlateBlue3": "#6959cd",
    "SlateBlue4": "#473c8b",
    "SlateGray": "#708090",
    "SlateGray1": "#c6e2ff",
    "SlateGray2": "#b9d3ee",
    "SlateGray3": "#9fb6cd",
    "SlateGray4": "#6c7b8b",
    "SlateGrey": "#708090",
    "SpringGreen": "#00ff7f",
    "SpringGreen1": "#00ff7f",
    "SpringGreen2": "#00ee76",
    "SpringGreen3": "#00cd66",
    "SpringGreen4": "#008b45",
    "SteelBlue": "#4682b4",
    "SteelBlue1": "#63b8ff",
    "SteelBlue2": "#5cacee",
    "SteelBlue3": "#4f94cd",
    "SteelBlue4": "#36648b",
    "VioletRed": "#d02090",
    "VioletRed1": "#ff3e96",
    "VioletRed2": "#ee3a8c",
    "VioletRed3": "#cd3278",
    "VioletRed4": "#8b2252",
    "WebGray": "#808080",
    "WebGreen": "#008000",
    "WebGrey": "#808080",
    "WebMaroon": "#800000",
    "WebPurple": "#800080",
    "WhiteSmoke": "#f5f5f5",
    "X11Gray": "#bebebe",
    "X11Green": "#00ff00",
    "X11Grey": "#bebebe",
    "X11Maroon": "#b03060",
    "X11Purple": "#a020f0",
    "YellowGreen": "#9acd32",
    "alice blue": "#f0f8ff",
    "antique white": "#faebd7",
    "aqua": "#00ffff",
    "aquamarine": "#7fffd4",
    "aquamarine1": "#7fffd4",
    "aquamarine2": "#76eec6",
    "aquamarine3": "#66cdaa",
    "aquamarine4": "#458b74",
    "azure": "#f0ffff",
    "azure1": "#f0ffff",
    "azure2": "#e0eeee",
    "azure3": "#c1cdcd",
    "azure4": "#838b8b",
    "beige": "#f5f5dc",
    "bisque": "#ffe4c4",
    "bisque1": "#ffe4c4",
    "bisque2": "#eed5b7",
    "bisque3": "#cdb79e",
    "bisque4": "#8b7d6b",
    "black": "#000000",
    "blanched almond": "#ffebcd",
    "blue violet": "#8a2be2",
    "blue": "#0000ff",
    "blue1": "#0000ff",
    "blue2": "#0000ee",
    "blue3": "#0000cd",
    "blue4": "#00008b",
    "brown": "#a52a2a",
    "brown1": "#ff4040",
    "brown2": "#ee3b3b",
    "brown3": "#cd3333",
    "brown4": "#8b2323",
    "burlywood": "#deb887",
    "burlywood1": "#ffd39b",
    "burlywood2": "#eec591",
    "burlywood3": "#cdaa7d",
    "burlywood4": "#8b7355",
    "cadet blue": "#5f9ea0",
    "chartreuse": "#7fff00",
    "chartreuse1": "#7fff00",
    "chartreuse2": "#76ee00",
    "chartreuse3": "#66cd00",
    "chartreuse4": "#458b00",
    "chocolate": "#d2691e",
    "chocolate1": "#ff7f24",
    "chocolate2": "#ee7621",
    "chocolate3": "#cd661d",
    "chocolate4": "#8b4513",
    "coral": "#ff7f50",
    "coral1": "#ff7256",
    "coral2": "#ee6a50",
    "coral3": "#cd5b45",
    "coral4": "#8b3e2f",
    "cornflower blue": "#6495ed",
    "cornsilk": "#fff8dc",
    "cornsilk1": "#fff8dc",
    "cornsilk2": "#eee8cd",
    "cornsilk3": "#cdc8b1",
    "cornsilk4": "#8b8878",
    "crimson": "#dc143c",
    "cyan": "#00ffff",
    "cyan1": "#00ffff",
    "cyan2": "#00eeee",
    "cyan3": "#00cdcd",
    "cyan4": "#008b8b",
    "dark blue": "#00008b",
    "dark cyan": "#008b8b",
    "dark goldenrod": "#b8860b",
    "dark gray": "#a9a9a9",
    "dark green": "#006400",
    "dark grey": "#a9a9a9",
    "dark khaki": "#bdb76b",
    "dark magenta": "#8b008b",
    "dark olive green": "#556b2f",
    "dark orange": "#ff8c00",
    "dark orchid": "#9932cc",
    "dark red": "#8b0000",
    "dark salmon": "#e9967a",
    "dark sea green": "#8fbc8f",
    "dark slate blue": "#483d8b",
    "dark slate gray": "#2f4f4f",
    "dark slate grey": "#2f4f4f",
    "dark turquoise": "#00ced1",
    "dark violet": "#9400d3",
    "deep pink": "#ff1493",
    "deep sky blue": "#00bfff",
    "dim gray": "#696969",
    "dim grey": "#696969",
    "dodger blue": "#1e90ff",
    "firebrick": "#b22222",
    "firebrick1": "#ff3030",
    "firebrick2": "#ee2c2c",
    "firebrick3": "#cd2626",
    "firebrick4": "#8b1a1a",
    "floral white": "#fffaf0",
    "forest green": "#228b22",
    "fuchsia": "#ff00ff",
    "gainsboro": "#dcdcdc",
    "ghost white": "#f8f8ff",
    "gold": "#ffd700",
    "gold1": "#ffd700",
    "gold2": "#eec900",
    "gold3": "#cdad00",
    "gold4": "#8b7500",
    "goldenrod": "#daa520",
    "goldenrod1": "#ffc125",
    "goldenrod2": "#eeb422",
    "goldenrod3": "#cd9b1d",
    "goldenrod4": "#8b6914",
    "green yellow": "#adff2f",
    "green": "#00ff00",
    "green1": "#00ff00",
    "green2": "#00ee00",
    "green3": "#00cd00",
    "green4": "#008b00",
    "honeydew": "#f0fff0",
    "honeydew1": "#f0fff0",
    "honeydew2": "#e0eee0",
    "honeydew3": "#c1cdc1",
    "honeydew4": "#838b83",
    "hot pink": "#ff69b4",
    "indian red": "#cd5c5c",
    "indigo": "#4b0082",
    "ivory": "#fffff0",
    "ivory1": "#fffff0",
    "ivory2": "#eeeee0",
    "ivory3": "#cdcdc1",
    "ivory4": "#8b8b83",
    "khaki": "#f0e68c",
    "khaki1": "#fff68f",
    "khaki2": "#eee685",
    "khaki3": "#cdc673",
    "khaki4": "#8b864e",
    "lavender blush": "#fff0f5",
    "lavender": "#e6e6fa",
    "lawn green": "#7cfc00",
    "lemon chiffon": "#fffacd",
    "light blue": "#add8e6",
    "light coral": "#f08080",
    "light cyan": "#e0ffff",
    "light goldenrod yellow": "#fafad2",
    "light goldenrod": "#eedd82",
    "light gray": "#d3d3d3",
    "light green": "#90ee90",
    "light grey": "#d3d3d3",
    "light pink": "#ffb6c1",
    "light salmon": "#ffa07a",
    "light sea green": "#20b2aa",
    "light sky blue": "#87cefa",
    "light slate blue": "#8470ff",
    "light slate gray": "#778899",
    "light slate grey": "#778899",
    "light steel blue": "#b0c4de",
    "light yellow": "#ffffe0",
    "lime green": "#32cd32",
    "lime": "#00ff00",
    "linen": "#faf0e6",
    "magenta": "#ff00ff",
    "magenta1": "#ff00ff",
    "magenta2": "#ee00ee",
    "magenta3": "#cd00cd",
    "magenta4": "#8b008b",
    "maroon": "#b03060",
    "maroon1": "#ff34b3",
    "maroon2": "#ee30a7",
    "maroon3": "#cd2990",
    "maroon4": "#8b1c62",
    "medium aquamarine": "#66cdaa",
    "medium blue": "#0000cd",
    "medium orchid": "#ba55d3",
    "medium purple": "#9370db",
    "medium sea green": "#3cb371",
    "medium slate blue": "#7b68ee",
    "medium spring green": "#00fa9a",
    "medium turquoise": "#48d1cc",
    "medium violet red": "#c71585",
    "midnight blue": "#191970",
    "mint cream": "#f5fffa",
    "misty rose": "#ffe4e1",
    "moccasin": "#ffe4b5",
    "navajo white": "#ffdead",
    "navy blue": "#000080",
    "navy": "#000080",
    "old lace": "#fdf5e6",
    "olive drab": "#6b8e23",
    "olive": "#808000",
    "orange red": "#ff4500",
    "orange": "#ffa500",
    "orange1": "#ffa500",
    "orange2": "#ee9a00",
    "orange3": "#cd8500",
    "orange4": "#8b5a00",
    "orchid": "#da70d6",
    "orchid1": "#ff83fa",
    "orchid2": "#ee7ae9",
    "orchid3": "#cd69c9",
    "orchid4": "#8b4789",
    "pale goldenrod": "#eee8aa",
    "pale green": "#98fb98",
    "pale turquoise": "#afeeee",
    "pale violet red": "#db7093",
    "papaya whip": "#ffefd5",
    "peach puff": "#ffdab9",
    "peru": "#cd853f",
    "pink": "#ffc0cb",
    "pink1": "#ffb5c5",
    "pink2": "#eea9b8",
    "pink3": "#cd919e",
    "pink4": "#8b636c",
    "plum": "#dda0dd",
    "plum1": "#ffbbff",
    "plum2": "#eeaeee",
    "plum3": "#cd96cd",
    "plum4": "#8b668b",
    "powder blue": "#b0e0e6",
    "purple": "#a020f0",
    "purple1": "#9b30ff",
    "purple2": "#912cee",
    "purple3": "#7d26cd",
    "purple4": "#551a8b",
    "rebecca purple": "#663399",
    "red": "#ff0000",
    "red1": "#ff0000",
    "red2": "#ee0000",
    "red3": "#cd0000",
    "red4": "#8b0000",
    "rosy brown": "#bc8f8f",
    "royal blue": "#4169e1",
    "saddle brown": "#8b4513",
    "salmon": "#fa8072",
    "salmon1": "#ff8c69",
    "salmon2": "#ee8262",
    "salmon3": "#cd7054",
    "salmon4": "#8b4c39",
    "sandy brown": "#f4a460",
    "sea green": "#2e8b57",
    "seashell": "#fff5ee",
    "seashell1": "#fff5ee",
    "seashell2": "#eee5de",
    "seashell3": "#cdc5bf",
    "seashell4": "#8b8682",
    "sienna": "#a0522d",
    "sienna1": "#ff8247",
    "sienna2": "#ee7942",
    "sienna3": "#cd6839",
    "sienna4": "#8b4726",
    "silver": "#c0c0c0",
    "sky blue": "#87ceeb",
    "slate blue": "#6a5acd",
    "slate gray": "#708090",
    "slate grey": "#708090",
    "snow": "#fffafa",
    "snow1": "#fffafa",
    "snow2": "#eee9e9",
    "snow3": "#cdc9c9",
    "snow4": "#8b8989",
    "spring green": "#00ff7f",
    "steel blue": "#4682b4",
    "tan": "#d2b48c",
    "tan1": "#ffa54f",
    "tan2": "#ee9a49",
    "tan3": "#cd853f",
    "tan4": "#8b5a2b",
    "teal": "#008080",
    "thistle": "#d8bfd8",
    "thistle1": "#ffe1ff",
    "thistle2": "#eed2ee",
    "thistle3": "#cdb5cd",
    "thistle4": "#8b7b8b",
    "tomato": "#ff6347",
    "tomato1": "#ff6347",
    "tomato2": "#ee5c42",
    "tomato3": "#cd4f39",
    "tomato4": "#8b3626",
    "turquoise": "#40e0d0",
    "turquoise1": "#00f5ff",
    "turquoise2": "#00e5ee",
    "turquoise3": "#00c5cd",
    "turquoise4": "#00868b",
    "violet red": "#d02090",
    "violet": "#ee82ee",
    "web gray": "#808080",
    "web green": "#008000",
    "web grey": "#808080",
    "web maroon": "#800000",
    "web purple": "#800080",
    "wheat": "#f5deb3",
    "wheat1": "#ffe7ba",
    "wheat2": "#eed8ae",
    "wheat3": "#cdba96",
    "wheat4": "#8b7e66",
    "white smoke": "#f5f5f5",
    "white": "#ffffff",
    "x11 gray": "#bebebe",
    "x11 green": "#00ff00",
    "x11 grey": "#bebebe",
    "x11 maroon": "#b03060",
    "x11 purple": "#a020f0",
    "yellow green": "#9acd32",
    "yellow": "#ffff00",
    "yellow1": "#ffff00",
    "yellow2": "#eeee00",
    "yellow3": "#cdcd00",
    "yellow4": "#8b8b00",
}


def parse_color(name: str) -> Color:
    """
    Parse a color string into a Textual Color object.

    This function acts as the main entry point for color parsing. It first
    attempts to parse the color using Textual's built-in `Color.parse()`",
    which handles modern formats like CSS names, rgb(), and hex codes.

    If that fails, it falls back to a lookup in the X11_NAMES dictionary to
    support the extended color names found in legacy terminals.

    Args:
        name: The color string to parse (e.g., "red", "#ff0000", "color(21)"",
              "DarkSlateGray4").

    Returns:
        A textual.color.Color object.

    Raises:
        ValueError: If the color string cannot be parsed.
    """
    from textual.color import Color

    # Implementation Note: This would first try Color.parse() and on failure",
    # would check the X11_NAMES dictionary.
    pass


# --- Palette Management Functions (Required) ---
# These functions are necessary because Textual does not have a concept of a
# dynamic, remappable 256-color palette. We must implement this logic to
# correctly handle escape sequences from applications that modify the palette
# (such as OSC 4).


def palette_init() -> list[Optional[Tuple[int, int, int]]]:
    """
    Initializes and returns a new 256-entry color palette.

    Each entry can hold an RGB tuple or be None if it's unset (default).
    This represents the terminal's internal palette state.

    Returns:
        A list of 256 None values.
    """
    pass


def palette_clear(palette: list) -> None:
    """
    Resets all entries in the given palette to their default (unset) state.

    This is used when an application sends a sequence to reset the palette.

    Args:
        palette: The palette list to clear.
    """
    pass


def palette_get(palette: list, index: int) -> Optional[Tuple[int, int, int]]:
    """
    Gets the currently defined RGB value for a palette index.

    If the color has not been dynamically redefined by an application, this
    should return None, indicating the terminal's default color for that
    index should be used.

    Args:
        palette: The palette list to query.
        index: The palette index (0-255).

    Returns:
        An RGB tuple (r, g, b) if set, otherwise None.
    """
    pass


def palette_set(palette: list, index: int, color: Tuple[int, int, int]) -> None:
    """
    Sets a new RGB value for a color in the palette.

    This is called when the emulator processes an escape sequence like OSC 4
    that redefines a palette color.

    Args:
        palette: The palette list to modify.
        index: The palette index to set (0-255).
        color: The new RGB tuple (r, g, b) for this index.
    """
    pass


# --- Unnecessary Functions (Handled by Textual) ---

# def color_join_rgb(r: int, g: int, b: int) -> Color:
#     """
#     REMOVED: This functionality is provided by the Textual Color constructor.
#
#     To create a color from RGB components, simply use:
#         `from textual.color import Color`
#         `my_color = Color(r, g, b)`
#     """
#     pass

# def color_split_rgb(color: Color) -> tuple[int, int, int]:
#     """
#     REMOVED: This functionality is provided by Textual Color object attributes.
#
#     To get RGB components from a Color object, access its properties:
#         `r, g, b = my_color.r, my_color.g, my_color.b`
#     """
#     pass

# def color_find_rgb(color: Color) -> int:
#     """
#     REMOVED: This functionality is provided by the `to_8_bit()` method.
#
#     To find the closest 8-bit (256 palette) color index for a truecolor
#     value, use:
#         `index = my_color.to_8_bit()`
#
#     Textual's implementation is also more perceptually accurate than the
#     simple Euclidean distance used in tmux.
#     """
#     pass

# def color_256toRGB(index: int) -> Color:
#     """
#     REMOVED: This functionality is provided by the `from_8_bit()` class method.
#
#     To convert a 256-palette index to its standard RGB color object, use:
#         `my_color = Color.from_8_bit(index)`
#     """
#     pass

# def color_256to16(color: Color) -> int:
#     """
#     REMOVED: This functionality is provided by the `to_4_bit()` method.
#
#     To downgrade a color to its closest 4-bit (16 color) equivalent, use:
#         `index_16_color = my_color.to_4_bit()`
#     """
#     pass

# def color_totheme(color: Color) -> str:
#     """
#     REMOVED: This functionality can be replicated using the `.luminance` property.
#
#     The original tmux function determined if a color was 'light' or 'dark'.
#     The same can be achieved more flexibly with Textual's Color objects:
#         `theme = "light" if my_color.luminance > 0.5 else "dark"`
#     """
#     pass

# def color_force_rgb(color: Color) -> Color:
#     """
#     REMOVED: This concept is implicit in Textual's design.
#
#     In Textual, all `Color` objects fundamentally represent a truecolor RGB
#     value internally. When a color like "red" or "color(21)" is parsed, it is
#     immediately converted to its RGB equivalent. There is no need for an
#     explicit conversion function.
#     """
#     pass
