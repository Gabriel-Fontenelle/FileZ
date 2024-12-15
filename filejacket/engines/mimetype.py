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


__all__ = ["MimeTypeEngine"]


class MimeTypeEngine:
    """
    Base class for handle MimeType. This call works mostly as common interface that must be overwritten to allow easy
    abstraction of methods to get extensions and mimetypes from distinct sources. Those sources can be from a library
    that save data on files, API or direct from databases.
    """

    @property
    def lossless_mimetypes(self) -> list[str]:
        """
        Method to return as attribute the mimetypes that are for lossless encoding.
        This method should be override in child class.
        """
        raise NotImplementedError(
            "lossless_mimetypes() method must be overwritten on child class."
        )

    @property
    def lossless_extensions(self) -> list[str]:
        """
        Method to return as attribute the extensions that are for lossless encoding.
        This method should be override in child class.
        """
        raise NotImplementedError(
            "lossless_extensions() method must be overwritten on child class."
        )

    @property
    def compressed_mimetypes(self) -> list[str]:
        """
        Method to return as attribute the mimetypes that are for containers of compression.
        This method should be override in child class.
        """
        raise NotImplementedError(
            "compressed_mimetypes() method must be overwritten on child class."
        )

    @property
    def compressed_extensions(self) -> list[str]:
        """
        Method to return as attribute the extensions that are for containers of compression.
        This method should be override in child class.
        """
        raise NotImplementedError(
            "compressed_extensions() method must be overwritten on child class."
        )

    @property
    def packed_extensions(self) -> list[str]:
        """
        Method to return as attribute the extensions that are for containers of compression.
        This method should be override in child class.
        """
        raise NotImplementedError(
            "packed_extensions() method must be overwritten on child class."
        )

    @staticmethod
    def sanitize_extension(extension: str):
        """
        Method to sanitize extension before using it.
        """
        return extension.lower()

    def get_extensions(self, mimetype: str) -> list[str]:
        """
        Method to get all registered extensions for given mimetype.
        This method should be override in child class.
        """
        raise NotImplementedError(
            "get_extensions() method must be overwritten on child class."
        )

    def get_mimetype(self, extension: str) -> str | None:
        """
        Method to get registered mimetype for given extension.
        This method should be override in child class.
        """
        raise NotImplementedError(
            "get_mimetype() method must be overwritten on child class."
        )

    def get_type(
        self, mimetype: str | None = None, extension: str | None = None
    ) -> None | str:
        """
        Method to get the associated type for the given mimetype or extension.
        This method should be override in child class.
        """
        raise NotImplementedError(
            "get_mimetype() method must be overwritten on child class."
        )

    def guess_extension_from_mimetype(self, mimetype: str) -> str | None:
        """
        Method to get the best extension for given mimetype in case there are more than one extension
        available.
        This method should be override in child class.
        """
        raise NotImplementedError(
            "guess_extension() method must be overwritten on child class."
        )

    def guess_extension_from_filename(self, filename: str) -> str | None:
        """
        Method to get the best extension for given filename in case there are more than one extension
        available using as base the filename that can or not have a registered extension in it.
        This method should be override in child class.
        """
        raise NotImplementedError(
            "guess_extension_and_mimetype() method must be overwritten on child class."
        )

    def is_extension_registered(self, extension: str) -> bool:
        """
        Method to check if a extension is registered or not in list of mimetypes and extensions.
        This method should be override in child class.
        """
        raise NotImplementedError(
            "is_extension_registered() method must be overwritten on child class."
        )

    def is_extension_lossless(self, extension: str) -> bool:
        """
        Method to check if a extension is related to a lossless file type or not.
        """
        return extension in self.lossless_extensions

    def is_mimetype_lossless(self, mimetype: str) -> bool:
        """
        Method to check if a mimetype is related to a lossless file type or not.
        """
        return mimetype in self.lossless_mimetypes

    def is_extension_compressed(self, extension: str) -> bool:
        """
        Method to check if an extension is related to a file that is container of compression or not.
        """
        return extension in self.compressed_extensions

    def is_extension_packed(self, extension: str) -> bool:
        """
        Method to check if an extension is related to a file that is extractable container of some sort.
        """
        return extension in self.packed_extensions

    def is_mimetype_compressed(self, mimetype: str) -> bool:
        """
        Method to check if a mimetype is related to a file that is container of compression or not.
        """
        return mimetype in self.compressed_mimetypes
