"""A3DS Stage 01: deterministic geometry, no GUI or Blender dependency."""
from .math3d import Vec3, Mat4
from .mesh import Mesh, MeshReport
from .surfaces import CrossSection, loft_sections
from .project import SurfaceProject

__all__ = ["Vec3", "Mat4", "Mesh", "MeshReport", "CrossSection", "loft_sections", "SurfaceProject"]
__version__ = "0.1.0"
