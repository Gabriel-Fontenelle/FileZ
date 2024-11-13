"""
Handler is a package for creating files in an object-oriented way, 
allowing extendability to any file system.

Copyright (C) 2021 Gabriel Fontenelle Senno Silva

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.

Should there be a need for contact the electronic mail
`filejacket <at> gabrielfontenelle.com` can be used.
"""

# Python internals
from __future__ import annotations

import re
from typing import Pattern
from uuid import uuid4

# modules
from .base import BaseRenamer


__all__ = ["WindowsRenamer", "LinuxRenamer", "UniqueRenamer"]


class WindowsRenamer(BaseRenamer):
    """
    Class following Windows style of renaming existing file to be used on Renamer pipelines.
    """

    enumeration_pattern: Pattern = re.compile(r" ?\([0-9]+\)$|\[[0-9]+\]$|$")

    @classmethod
    def get_name(
        cls, directory_path: str, filename: str, extension: str | None
    ) -> tuple[str, str | None]:
        """
        Method to get the new generated name.
        If there is a duplicated name the new name will follow
        the style of Windows: `new name (1).ext`
        """
        # Prepare filename and extension removing enumeration from filename
        # and setting up a empty string is extension is None
        filename = cls.enumeration_pattern.sub("", filename)
        formatted_extension: str = f".{extension}" if extension else ""

        i = 0
        while cls.file_system_handler.exists(
            directory_path + filename + formatted_extension
        ) or cls.is_name_reserved(filename, formatted_extension):
            i += 1
            filename = cls.enumeration_pattern.sub(f" ({i})", filename)

        return filename, extension


class LinuxRenamer(BaseRenamer):
    """
    Class following Linux style of renaming existing file to be used on BaseRenamer pipelines.
    """

    enumeration_pattern: Pattern = re.compile(r"( +)?\- +[0-9]+$|$")

    @classmethod
    def get_name(
        cls, directory_path: str, filename: str, extension: str | None
    ) -> tuple[str, str | None]:
        """
        Method to get the new generated name.
        If there is a duplicated name the new name will follow
        the style of Linux: `new name - 1.ext`
        """
        # Prepare filename and extension removing enumeration from filename
        # and setting up a empty string is extension is None
        filename = cls.enumeration_pattern.sub("", filename)
        formatted_extension: str = f".{extension}" if extension else ""

        i = 0
        while cls.file_system_handler.exists(
            directory_path + filename + formatted_extension
        ) or cls.is_name_reserved(filename, formatted_extension):
            i += 1
            filename = cls.enumeration_pattern.sub(f" - {i}", filename)

        return filename, extension


class UniqueRenamer(BaseRenamer):
    @classmethod
    def get_name(
        cls, directory_path: str, filename: str, extension: str | None
    ) -> tuple[str, str | None]:
        """
        Method to get the new generated name. The new name will be the UUID version 4.
        This method will throw a BlockingIOError if there is more then
        100 tries to generate a unique UUID4.
        """
        formatted_extension: str = f".{extension}" if extension else ""

        # Generate Unique filename
        filename = str(uuid4())

        i = 0
        while (
            cls.file_system_handler.exists(
                directory_path + filename + formatted_extension
            )
            or cls.is_name_reserved(filename, formatted_extension)
        ) and i < 100:
            i += 1
            # Generate Unique filename
            filename = str(uuid4())

        if i == 100:
            raise BlockingIOError("Too many files being handled simultaneous!")

        return filename, extension
