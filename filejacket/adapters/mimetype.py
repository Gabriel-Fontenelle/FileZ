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
# first-party
from __future__ import annotations

from typing import TYPE_CHECKING

import mimetypes
from os.path import dirname, realpath, join, exists
import re

from ..engines.mimetype import MimeTypeEngine

if TYPE_CHECKING:
    from typing import Pattern


__all__ = ["LibraryMimeTyper", "APIMimeTyper"]


class LibraryMimeTyper(MimeTypeEngine):
    """
    Class for handling MimeTypes using the mimetypes library of python. This class will load its mimetype
    from an updated `mime.types` file in data directory.
    """

    _known_mimetypes_file: str = join(
        dirname(dirname(realpath(__file__))), "data", "mime.types"
    )
    """
    Path of file `mime.types` to be loaded of known mimetypes.
    """
    _pattern_split_package: Pattern = re.compile(r"^[rz][0-9]+$", flags=re.IGNORECASE)

    def __init__(self) -> None:
        """
        Method that instantiate the mimetype library and load to it the file of known mimetypes.
        It will output a IOError, that must be caught in stack above, if file don't exists.
        """
        assert exists(self._known_mimetypes_file)
        mimetypes.init(files=[self._known_mimetypes_file])

    @property
    def lossless_mimetypes(self) -> list[str]:
        """
        Method to return as attribute the mimetypes that are for lossless encoding.
        """
        return [
            "audio/mp4",
            "audio/x-caf",
            "audio/x-flac",
            "audio/x-ms-wma",
            "audio/x-oma",
            "audio/x-pn-realaudio",
            "audio/x-wav",
            "image/raw",
            "video/raw",
        ]

    @property
    def lossless_extensions(self) -> list[str]:
        """
        Method to return as attribute the extensions that are for lossless encoding.
        """
        return [
            "3fr",
            "aa3",
            "ari",
            "arw",
            "at3",
            "at9",
            "avif",
            "bay",
            "braw",
            "bz2",
            "caf",
            "cap",
            "cr2",
            "cr3",
            "crw",
            "data",
            "dcr",
            "dcs",
            "dng",
            "drf",
            "eip",
            "erf",
            "fff",
            "flac",
            "flif",
            "gpr",
            "iiq",
            "k25",
            "kdc",
            "m4a",
            "mdc",
            "mef",
            "mlp",
            "mos",
            "mp4a",
            "mrw",
            "nef",
            "nrw",
            "obm",
            "oma",
            "orf",
            "osq",
            "pef",
            "ptx",
            "pxn",
            "r3d",
            "raf",
            "raw",
            "rw2",
            "rwl",
            "rwz",
            "sr2",
            "srf",
            "srw",
            "tif",
            "wav",
            "x3f",
        ]

    @property
    def compressed_mimetypes(self) -> list[str]:
        """
        Method to return as attribute the mimetypes that are for containers of compression.
        """
        return [
            "application/cz",
            "application/epub+zip",
            "application/gzip",
            "application/java-archive",
            "application/rar",
            "application/vnd.apple.installer+xm",
            "application/vnd.ezpix-album",
            "application/vnd.ezpix-package",
            "application/x-7z-compressed",
            "application/x-cbr",
            "application/x-debian-package",
            "application/x-dgc-compressed",
            "application/x-gtar",
            "application/x-gzip",
            "application/x-rar",
            "application/x-rar-compressed",
            "application/x-tar",
            "application/zip",
            "application/zlib",
        ]

    @property
    def compressed_extensions(self) -> list[str]:
        """
        Method to return as attribute the extensions that are for containers of compression.
        """
        return [
            "7z",
            "abr",
            "cb7",
            "cba",
            "cbr",
            "cbt",
            "cbz" "cz",
            "deb",
            "dgc",
            "ez2",
            "ez3",
            "gtar",
            "gz",
            "jar",
            "mpkg",
            "msi",
            "rar",
            "tar",
            "zip",
        ]

    @property
    def packed_extensions(self) -> list[str]:
        """
        Method to return as attribute the extensions that are for extractable containers of some sort.
        """
        return self.compressed_extensions + [
            "psd",
            "epub",
            "mkv",
            "mka",
        ]

    def get_extensions(self, mimetype: str) -> list[str]:
        """
        Method to get all registered extensions for given mimetype.
        Because mimetypes.guess_all_extensions return extensions with dot in the begin we should remove it from
        extensions.
        """
        return [
            extension[1:]
            for extension in mimetypes.guess_all_extensions(mimetype, False)
        ]

    def get_mimetype(self, extension: str) -> str | None:
        """
        Method to get registered mimetype for given extension.
        """
        # Fix for partial file
        if self._pattern_split_package.match(extension):
            match extension[0]:
                case "r":
                    extension = "rar"
                case "z":
                    extension = "zip"

        return mimetypes.types_map.get(f".{self.sanitize_extension(extension)}", None)

    def get_type(
        self, mimetype: str | None = None, extension: str | None = None
    ) -> None | str:
        """
        Method to get the associated type for the given mimetype or extension.
        """
        if not (mimetype and extension):
            raise ValueError(
                "mimetype or extension must be informed at LibraryMimeTyper.get_type."
            )

        # Set-up list of types available from file `mime.types` as a set.
        known_types: set[str] = {
            "application",
            "audio",
            "binary",
            "chemical",
            "image",
            "interface",
            "message",
            "model",
            "multipart",
            "text",
            "video",
            "x-conference",
        }

        if extension and not mimetype:
            mimetype = self.get_mimetype(extension)

        if not mimetype:
            return None

        # Get set from mimetype using a list of first element before `/` in mimetype.
        possible_type: list[str] = mimetype.split("/", 1)[:1]
        possible_type_set = set(possible_type)

        return possible_type[0] if possible_type_set.intersection(known_types) else None

    def guess_extension_from_mimetype(self, mimetype: str) -> str | None:
        """
        Method to get the best extension for given mimetype in case there are more than one extension
        available.
        As extensions are getted from file that storage ony extensions and mimetype there is way to tell
        which one if better suited for the mimetype, so we return the first one. Except for jpg, we return it instead
        of jpe and alternatives.
        """
        extensions: list = self.get_extensions(mimetype)

        if not extensions:
            return None

        # Fix for jpe being returned instead of jpg.
        if "jpg" in extensions:
            return "jpg"
        if "mp4" in extensions:
            return "mp4"

        return extensions[0]

    def guess_extension_from_filename(self, filename: str) -> str | None:
        """
        Method to get the best extension for given filename in case there are more than one extension
        available using as base the filename that can or not have a registered extension in it.
        """
        splitted: list[str] = filename.rsplit(".", 1)
        maybe_extension: str = splitted[int(len(splitted) == 2)]

        if maybe_extension and self.is_extension_registered(maybe_extension):
            return maybe_extension

        return None

    def is_extension_registered(self, extension: str) -> bool:
        """
        Method to check if an extension is registered or not in list of mimetypes and extensions.
        """
        return bool(self.get_mimetype(self.sanitize_extension(extension)))


class APIMimeTyper(MimeTypeEngine):
    """
    Class for handling MimeTypes using an external API. This class should use a cache to avoid consuming the API
    every time that a mimetype or extension must be guessed.

    TODO: Override BaseMimeTyper methods with methods that call a external API.
    """
