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

from typing import Any, Type

from ...pipelines import Pipeline
from ...file import FileThumbnail, FileHashes, FileContent, FilePacket


__all__ = [
    "serialize_pipeline",
    "serialize_datetime",
    "serialize_class",
    "serialize_object_class",
    "serialize_attribute",
    "serialize_hashes",
    "serialize__thumbnail",
    "serialize__content",
    "serialize__content_files",
    "serialize_value"
]

def serialize_pipeline(value: Pipeline) -> dict[str, Any]:
    return {
        "pipeline": serialize_class(value.__class__),
        "processor": serialize_class(value.processor),
        "processors_candidate": value.processors_candidate
    }


def serialize_datetime(value: datetime | time) -> str:
    return value.isoformat()


def serialize_class(value: Type) -> str:
    return f"{value.__module__}.{value.__name__}"


def serialize_object_class(value: Type) -> dict[str, str]:
    return f"{value.__class__.__module__}.{value.__class__.__name__}"


def serialize_attribute(value: object) -> dict[str, Any]:
    dict_to_return = value.__serialize__

    if 'related_file_object' in dict_to_return:
        del dict_to_return['related_file_object']

    return dict_to_return


def serialize_hashes(value: FileHashes) -> dict[str, Any]:
    hashes = value.__serialize__

    cache = {}
    for hash_name, hash_tuple in hashes['_cache']:
        cache[hash_name] = (
            hash_tuple[0], FileSerializer.serialize(hash_tuple[1]), serialize_class(hash_tuple[2])
        )

    # We don`t need `_loaded` neither `related_file_object` as they can be inferred from _cache and file object.
    return cache


def serialize__thumbnail(value: FileThumbnail) -> dict[str, Any]:
    thumbnail = value.__serialize__

    # Convert _static_file and _animated_file to Base64
    static_file = thumbnail["_static_file"].content_as_base64 if thumbnail["_static_file"] else None
    animated_file = thumbnail["_animated_file"].content_as_base64 if thumbnail["_animated_file"] else None

    return {
        "static_defaults": serialize_class(thumbnail["static_defaults"]),
        "animated_defaults": serialize_class(thumbnail["animated_defaults"]),
        "static_file": static_file,
        "animated_file": animated_file,
        "image_engine": serialize_class(thumbnail["image_engine"]),
        "video_engine": serialize_class(thumbnail["video_engine"]),
        "render_static_pipeline": serialize_pipeline(thumbnail["render_static_pipeline"]),
        "render_animated_pipeline": serialize_pipeline(thumbnail["render_animated_pipeline"])
    }


def serialize__content(value: FileContent) -> dict[str, Any]:
    pass


def serialize__content_files(value: FilePacket):
    # Case should cache convert to base64
    content_files = value.__serialize__
    # TODO: Change this import to be relative at FilePacket related file.
    from . import FileSerializer

    return {
        "internal_files": {
            key: FileSerializer.serialize(value)
            for key, value in content_files["_internal_files"].items()
        },
        "unpack_data_pipeline": serialize_pipeline(content_files["unpack_data_pipeline"])
    }


def serialize_value(value: Any) -> Any:
    return value
