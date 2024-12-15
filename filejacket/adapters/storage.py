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

import os
import re
from datetime import datetime
from os.path import (
    getctime,
    normcase,
    normpath,
)
from pathlib import Path, WindowsPath, PosixPath

# third-party
from typing import Any, Pattern

from ..engines.storage import StorageEngine


__all__ = [
    "WindowsFileSystem",
    "LinuxFileSystem",
]


class WindowsFileSystem(StorageEngine):
    """
    Class that standardized methods of file systems for Windows Operational System.
    """

    temporary_folder: str = "C:\\temp\\FileJacket"
    """
    Define the location of temporary content in filesystem.
    """
    file_sequence_style: tuple[Pattern[str], str] = (
        re.compile(r"(\ *\(\d+?\))?(\.[^.]*$)"),
        r" ({sequence})\2",
    )
    """
    Define the pattern to use to replace a sequence in the stylus of the filesystem.
    The first part identify the search and the second the replace value.
    This allow search by `<str>.<str>` and replace by `<str> (<int>).<str>`.
    """
    new_line = "\r\n"
    """
    Define the character for breaking line in the file system.
    This override the default one for Unix `\n`.
    """

    @classmethod
    def get_path_id(cls, path: str) -> str:
        """
        Method to get the file system id for a path.
        Path can be both a directory or file.

        TODO: Test it at Windows.
        """
        # TODO: Conclude function after testing on Windows.
        file = r"C:\Users\Grandmaster\Desktop\testing.py"
        output = os.popen(rf"fsutil file queryfileid {file}").read()

        return str(output)

    @classmethod
    def get_created_date(cls, path: str) -> datetime:
        """
        Try to get the date that a file was created, falling back to when it was
        last modified if that isn't possible.
        See https://stackoverflow.com/a/39501288/1709587 for explanation.
        Source: https://stackoverflow.com/a/39501288
        """
        time = getctime(path)

        return datetime.fromtimestamp(time)

    @classmethod
    def sanitize_path(cls, path: str) -> str:
        """
        Method to normalize a path for use.
        This method collapse redundant separators and up-level references so that A//B, A/B/, A/./B and A/foo/../B
        all become A/B. It will also convert uppercase character to lowercase and `/` to `\\`.
        """
        return normpath(normcase(path))

    @classmethod
    def get_pathlib_path(cls, path: str) -> Path:
        """
        Method to get the custom Path class with accessor override.
        """

        class CustomPath(WindowsPath):
            def open(self, *args: Any, **kwargs: Any) -> Any:
                return cls.opener(*args, **kwargs)

            def listdir(self, *args: Any, **kwargs: Any) -> Any:
                return cls.list_files_and_directories(*args, **kwargs)

            def mkdir(self, *args: Any, **kwargs: Any) -> Any:
                return cls.create_directory(*args, **kwargs)

            def rmdir(self, *args: Any, **kwargs: Any) -> Any:
                return cls.delete(*args, **kwargs)

            def rename(self, *args: Any, **kwargs: Any) -> Any:
                return cls.rename(*args, **kwargs)

            def replace(self, *args: Any, **kwargs: Any) -> Any:
                return cls.replace(*args, **kwargs)

        return CustomPath(path)


class LinuxFileSystem(StorageEngine):
    """
    Class that standardized methods of file systems for Linux Operational System.
    """

    temporary_folder: str = "/tmp/FileJacket"
    """
    Define the location of temporary content in filesystem.
    """
    file_sequence_style: tuple[Pattern[str], str] = (
        re.compile(r"(\ *-\ *\d+?)?(\.[^.]*$)"),
        r" - {sequence}\2",
    )
    """
    Define the pattern to use to replace a sequence in the stylus of the filesystem.
    The first part identify the search and the second the replace value.
    This allow search by `<str>.<str>` and replace by `<str> - <int>.<str>`.
    """

    @classmethod
    def get_path_id(cls, path: str) -> str:
        """
        Method to get the file system id for a path.
        Path can be both a directory or file.
        """
        return str(os.stat(path, follow_symlinks=False).st_ino)

    @classmethod
    def get_created_date(cls, path: str) -> datetime:
        """
        Try to get the date that a file was created, falling back to when it was
        last modified if that isn't possible.
        See https://stackoverflow.com/a/39501288/1709587 for explanation.
        Source: https://stackoverflow.com/a/39501288
        """
        stats = os.stat(path)
        try:
            time = stats.st_birthtime
        except AttributeError:
            # We're probably on Linux. No easy way to get creation dates here,
            # so we'll settle for when its content was last modified.
            time = stats.st_mtime

        return datetime.fromtimestamp(time)

    @classmethod
    def get_pathlib_path(cls, path: str) -> Path:
        """
        Method to get the custom Path class with accessor override.
        """

        class CustomPath(PosixPath):
            def open(self, *args: Any, **kwargs: Any) -> Any:
                return cls.opener(*args, **kwargs)

            def listdir(self, *args: Any, **kwargs: Any) -> Any:
                return cls.list_files_and_directories(*args, **kwargs)

            def mkdir(self, *args: Any, **kwargs: Any) -> Any:
                return cls.create_directory(*args, **kwargs)

            def rmdir(self, *args: Any, **kwargs: Any) -> Any:
                return cls.delete(*args, **kwargs)

            def rename(self, *args: Any, **kwargs: Any) -> Any:
                return cls.rename(*args, **kwargs)

            def replace(self, *args: Any, **kwargs: Any) -> Any:
                return cls.replace(*args, **kwargs)

        return CustomPath(path)
