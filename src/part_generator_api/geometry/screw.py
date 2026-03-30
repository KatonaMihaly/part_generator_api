import json
from importlib.resources import files

from build123d import Cylinder, Location

from part_generator_api.geometry.base import BaseGeometry

# ISO 4762:2004 / DIN 912 - Socket Head Cap Screw nominal dimensions
# Format: nominal_diameter_d: (head_diameter_dk, head_height_k) [mm]
_raw = json.loads(files("part_generator_api.data").joinpath("iso_4762.json").read_text())
ISO_4762_HEAD = {float(k): v for k, v in _raw.items()}


class ScrewGenerator(BaseGeometry):
    """
    FEM-optimised (no champfer, no thread) socket head cap screw.
    """

    def __init__(self, diameter, length):
        self.diameter = diameter
        self.length = length

    def generate(self):
        """
        Ensured that the anchor point is on the bottom face centerpoint of the shank.
        """
        entry = ISO_4762_HEAD[self.diameter]
        dk, k = entry["dk"], entry["k"]
        shank = Cylinder(radius=self.diameter / 2, height=self.length).locate(
            Location((0, 0, self.length / 2))
        )
        head = Cylinder(radius=dk / 2, height=k).locate(
            Location((0, 0, self.length + k / 2))
        )
        return head + shank
