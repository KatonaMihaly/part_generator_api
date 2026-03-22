from build123d import Cylinder, Location, Shape

from part_generator_api.geometry.base import BaseGeometry

# ISO 4762:2004 / DIN 912 — Socket Head Cap Screw nominal dimensions
# Format: nominal_diameter_d → (head_diameter_dk, head_height_k)  [mm]
# Source: ISO 4762:2004 Table 1, nominal (max) values
ISO_4762_HEAD = {
    1.6: (3.00,  1.60),
    2:   (3.80,  2.00),
    2.5: (4.50,  2.50),
    3:   (5.50,  3.00),
    4:   (7.00,  4.00),
    5:   (8.50,  5.00),
    6:   (10.00, 6.00),
    8:   (13.00, 8.00),
    10:  (16.00, 10.00),
    12:  (18.00, 12.00),
    14:  (21.00, 14.00),
    16:  (24.00, 16.00),
    18:  (27.00, 18.00),
    20:  (30.00, 20.00),
    22:  (33.00, 22.00),
    24:  (36.00, 24.00),
    27:  (40.00, 27.00),
    30:  (45.00, 30.00),
    36:  (54.00, 36.00),
    42:  (63.00, 42.00),
    48:  (72.00, 48.00),
    56:  (84.00, 56.00),
    64:  (96.00, 64.00),
}


class ScrewGenerator(BaseGeometry):
    """FEM-simplified socket head cap screw (ISO 4762)."""

    def __init__(self, diameter, length):
        self.diameter = diameter
        self.length = length

    def generate(self):
        dk, k = ISO_4762_HEAD[self.diameter]
        shank = Cylinder(radius=self.diameter / 2, height=self.length).locate(
            Location((0, 0, self.length / 2))
        )
        head = Cylinder(radius=dk / 2, height=k).locate(
            Location((0, 0, self.length + k / 2))
        )
        return head + shank
