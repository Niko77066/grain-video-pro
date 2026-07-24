"""Kuleshov Film IR API（M1）——film.json 的受管读写、G1 硬门与执行入口。

    from film_ir import ir_read, ir_patch, ir_validate, ir_execute
"""

from .api import ir_execute, ir_migrate, ir_new, ir_patch, ir_read, ir_validate
from .errors import IRError
from .models import SCHEMA_VERSION, FilmIR

__version__ = "0.1.0"
__all__ = ["ir_read", "ir_patch", "ir_validate", "ir_execute", "ir_new",
           "ir_migrate", "IRError", "FilmIR", "SCHEMA_VERSION"]
