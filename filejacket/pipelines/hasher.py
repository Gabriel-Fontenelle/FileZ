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

import hashlib
from typing import Any

from zlib import crc32

# modules
from .base import BaseHasher


__all__ = ["BaseHasher", "CRC32Hasher", "MD5Hasher", "SHA256Hasher"]


class MD5Hasher(BaseHasher):
    """
    Class specifying algorithm MD5 to be used on Hasher pipelines.
    """

    hasher_name: str = "md5"
    """
    Name of hasher algorithm and also its extension abbreviation.
    """

    @classmethod
    def instantiate_hash(cls) -> Any:
        """
        Method to instantiate the hash generator to be used digesting the hash.
        """
        return hashlib.md5()


class SHA256Hasher(BaseHasher):
    """
    Class specifying algorithm SHA256 to be used on Hasher pipelines.
    """

    hasher_name: str = "sha256"
    """
    Name of hasher algorithm and also its extension abbreviation.
    """

    @classmethod
    def instantiate_hash(cls) -> Any:
        """
        Method to instantiate the hash generator to be used digesting the hash.
        """
        return hashlib.sha256()


class CRC32Hasher(BaseHasher):
    """
    Class specifying algorithm CRC32 to be used on Hasher pipelines.
    """

    hasher_name: str = "crc32"
    """
    Name of hasher algorithm and also its extension abbreviation.
    """

    @classmethod
    def instantiate_hash(cls) -> dict[str, str]:
        """
        Method to instantiate the hash generator to be used digesting the hash.
        """
        return {"crc32": "0"}

    @classmethod
    def digest_hash(cls, hash_instance: dict[str, Any]) -> str:
        """
        Method to digest the hash generated at hash_instance.
        As CRC32 don't work as hashlib we used the instantiate_hash to start a dictionary
        for the sum of the digested hash.
        """
        return hash_instance["crc32"]

    @classmethod
    def digest_hex_hash(cls, hash_instance: dict[str, Any]) -> str:
        """
        Method to digest the hash generated at hash_instance.
        """
        return hash_instance["crc32"]

    @classmethod
    def update_hash(
        cls,
        hash_instance: dict[str, Any],
        content: bytes | str,
        encoding: str = "utf-8",
    ) -> None:
        """
        Method to update content in hash_instance to generate the hash. We convert all content to bytes to
        generate a hash of it.
        """
        if isinstance(content, str):
            content = content.encode(encoding)

        hash_instance["crc32"] = str(crc32(content, hash_instance["crc32"]))
