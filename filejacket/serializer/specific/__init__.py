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
`filez <at> gabrielfontenelle.com` can be used.
"""
from __future__ import annotations

from collections import namedtuple
from typing import Any, Type, TYPE_CHECKING

from ...storage import LinuxFileSystem
from ...file import BaseFile

from .serialize_to import *

if TYPE_CHECKING:
    from .storage import Storage


__all__ = [
    'FileSerializer',
    'FileSerializerContent',
    'FileSerializerToJson',
    'FileSerializerContentToJson',
]


# NamedTuple to allow better organization of validation without using too much `if else`.
ConverterCondition = namedtuple("ConverterCondition", ["attribute_name", "converter"])
# NamedTuple to allow better organization of what to ignore on URI without using too
# much `if else`.


class SerializerJsonMixin:
    """

    """

    @classmethod
    def serialize(cls, source: BaseFile) -> str:
        """

        """
        from json import dumps
        dict_to_convert = super().serialize(source=source)

        return dumps(dict_to_convert)

    @classmethod
    def deserialize(cls, source: str) -> BaseFile:
        """

        """
        from json import loads

        dict_to_parse = loads(source)

        return super().deserialize(source=dict_to_parse)


class FileSerializer:
    """
    Class that allow handling of Serialization/Deserialization from BaseFile instance to and from a json string.
    This class was created with specificity in mind and would need to be override if the object to be serializaded is
    has a custom class based on BaseFile.
    """

    serialization_condition = [
        # Datetime attributes
        ConverterCondition("create_date", serialize_datetime),
        ConverterCondition("update_date", serialize_datetime),
        # Class attributes
        ConverterCondition("storage", serialize_class),
        ConverterCondition("serializer", serialize_class),
        ConverterCondition("uri_handler", serialize_class),

        ConverterCondition("mime_type_handler", serialize_object_class),

        ConverterCondition("extract_data_pipeline", serialize_pipeline),
        ConverterCondition("compare_pipeline", serialize_pipeline),
        ConverterCondition("hasher_pipeline", serialize_pipeline),
        ConverterCondition("rename_pipeline", serialize_pipeline),
        ConverterCondition("compare_pipeline", serialize_pipeline),

        ConverterCondition("_option", serialize_attribute),
        ConverterCondition("_actions", serialize_attribute),
        ConverterCondition("_naming", serialize_attribute),
        ConverterCondition("_state", serialize_attribute),
        ConverterCondition("_meta", serialize_attribute),

        ConverterCondition("_content_files", serialize__content_files),
        ConverterCondition("_thumbnail", serialize__thumbnail),
        ConverterCondition("hashes", serialize_hashes),
        ConverterCondition("_content", serialize__content),

        ConverterCondition("id", serialize_value),
        ConverterCondition("filename", serialize_value),
        ConverterCondition("extension", serialize_value),
        ConverterCondition("_path", serialize_value),
        ConverterCondition("_save_to", serialize_value),
        ConverterCondition("relative_path", serialize_value),
        ConverterCondition("length", serialize_value),
        ConverterCondition("mime_type", serialize_value),
        ConverterCondition("type", serialize_value),
        ConverterCondition("__version__", serialize_value)
    ]

    @classmethod
    def serialize(cls, source: BaseFile) -> dict[str, str | int | bool]:
        """
        Method to serialize the input `source` using dill as extension to `pickle`.
        """
        return {
            condition.attribute: condition.converter(source.__serialize__[condition.attribute])
            for condition in cls.serialization_condition
        }

    @classmethod
    def deserialize(cls, source: dict[str, Any]) -> BaseFile:
        """
        Method to deserialize the input `source` using dill as extension to `pickle`.
        """
        pass


class FileSerializerContent(FileSerializer):
    """

    """

    serialization_condition = [
        condition for condition in FileSerializer.serialization_condition
        if condition.attribute != "_content"
    ] + [ConverterCondition("_content", serialize__content_base64)]


class FileSerializerToJson(SerializerJsonMixin, FileSerializer):
    pass


class FileSerializerContentToJson(SerializerJsonMixin, FileSerializerContent):
    pass
