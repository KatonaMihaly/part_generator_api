from build123d import Cylinder, Location

from part_generator_api.geometry.base import BaseGeometry


class WasherGenerator(BaseGeometry):
    """
    FEM-optimised (no chamfer) washer.
    """
    def __init__(self, inner_diameter, outer_diameter, thickness):
        self.inner_diameter = inner_diameter
        self.outer_diameter = outer_diameter
        self.thickness = thickness

    def generate(self):
        """
        Ensures that the anchor point is on the bottom face centerpoint of the washer.
        """
        outer = Cylinder(radius=self.outer_diameter / 2, height=self.thickness).locate(
            Location((0, 0, self.thickness / 2))
        )
        inner = Cylinder(radius=self.inner_diameter / 2, height=self.thickness).locate(
            Location((0, 0, self.thickness / 2))
        )
        return outer - inner
