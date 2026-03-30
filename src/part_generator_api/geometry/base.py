import os
import tempfile
from abc import ABC, abstractmethod

from build123d import Shape, export_step


class BaseGeometry(ABC):
    """
    Ensures that all subclasses (parts) inherit these common methods.
    """

    @abstractmethod
    def generate(self):
        """
        Ensures that all subclasses (part) define a generate method uniquely.
        """
        pass

    def to_step_bytes(self):
        shape = self.generate()
        # export_step() requires a file path (BytesIO not supported by OpenCascade)
        # the workaround is to create a local, temporary .step and read it back to bytes
        with tempfile.NamedTemporaryFile(suffix=".step", delete=False) as f:
            tmp_path = f.name
        try:
            export_step(shape, tmp_path)
            with open(tmp_path, "rb") as f:
                return f.read()
        finally:
            os.unlink(tmp_path)
