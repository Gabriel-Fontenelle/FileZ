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
from __future__ import annotations

from base64 import b64decode
from datetime import datetime, time
from typing import Any, Type, TYPE_CHECKING
from importlib import import_module

from filejacket.exception import SerializerError
from filejacket.file.content import FileContent, FilePacket
from filejacket.file.hash import FileHashes
from filejacket.file.thumbnail import FileThumbnail

from ..pipelines import Pipeline

if TYPE_CHECKING:
    from ..file import BaseFile


__all__ = [
    # Transmuters
    'Transmuter',
    'TransmuterClass',
    'TransmuterObjectClass',
    'TransmuterPipeline',
    'TransmuterDatetime',
    'TransmuterAttribute',
    'TransmuterValue',
    'TransmuterThumbnail',
    'TransmuterHashes',
    'TransmuterContentFiles',
    'TransmuterContent',
    'TransmuterContentBase64',
    # Serializers
    'FileDictionarySerializer',
    'FileWithContentDictionarySerializer',
    'FileJsonSerializer',
    'FileWithContentJsonSerializer',
]


class Transmuter:
    """
    Class helper for converting values at serializer/deserializer classes that made use of it in its declareted attributes.
    This class uses __set_name__ as a way to organize the code and reference to those classes.
    """

    def __set_name__(self, owner, name):
        """
        Method to automatically set the attribute name in which it was declared and register it in owner list of attributes.
        The owner list of attributes will be created at the first call of a class that inherent Transmuter.

        Usage:
        
        ```
        class Serializer:
            my_attribute = Transmuter()
        
        ```
        """
        
        self.attribute_name = name
        self.serializer = owner
        
        if hasattr(owner, 'transmuters'):
            owner.transmuters.add(name)
        else:
            owner.transmuters = {name}
    
    @classmethod
    def from_data(cls, value: Any) -> Any:
        """
        Method for the transmuter to serialize a value. 
        This Method should be override in child classes.
        """
        raise NotImplementedError("The method `from_data` must be implemented in child class.")
    
    @classmethod
    def to_data(cls, value: Any, reference: BaseFile) -> Any:
        """
        Method for the transmuter to deserialize a value. 
        This Method should be override in child classes.
        """
        raise NotImplementedError("The method `to_data` must be implemented in child class.")
    

class TransmuterClass(Transmuter):
    """
    Transmuter class to handle uninstantiated class. 
    """
    
    @classmethod
    def from_data(cls, value: Type) -> str:
        """
        Method to convert `value` to string for use in dict.
        """
        return f"{value.__module__}.{value.__name__}"
    
    @classmethod
    def to_data(cls, value: str, reference: BaseFile) -> Type:
        """
        Method to reverse the conversion at `from_data`.
        """
        module_name, class_name = value.rsplit('.', maxsplit=1)
        module = import_module(module_name)
        return getattr(module, class_name)
    

class TransmuterObjectClass(Transmuter):
    """
    Transmuter class to handle instantiated class. 
    """
    
    @classmethod
    def from_data(cls, value: object) -> str:
        """
        Method to convert `value` to string for serialization.
        """
        return f"{value.__class__.__module__}.{value.__class__.__name__}"

    @classmethod
    def to_data(cls, value: str, reference: BaseFile) -> object:
        """
        Method to reverse the conversion at `from_data`.
        """
        module_name, class_name = value.rsplit('.', maxsplit=1)
        module = import_module(module_name)
        return getattr(module, class_name)()


class TransmuterPipeline(Transmuter):
    """
    Transmuter class to handle Pipeline objects. 
    """
    
    @classmethod
    def from_data(cls, value: Pipeline) -> dict[str, str | list[str]]:
        """
        Method to convert `value` to dict for serialization.
        """
        return {
            "pipeline": TransmuterClass.from_data(value.__class__),
            "processor": TransmuterClass.from_data(value.processor),
            "processors_candidate": value.processors_candidate
        }
    
    @classmethod
    def to_data(cls, value: dict[str, Any], reference: BaseFile) -> Pipeline:
        """
        Method to reverse the conversion at `from_data`.
        """
        pipeline = TransmuterClass.to_data(value["pipeline"], reference=reference)(*value["processors_candidate"])
        pipeline.processor = TransmuterClass.to_data(value["processor"], reference=reference)

        return pipeline


class TransmuterDatetime(Transmuter):
    """
    Transmuter class to handle datetime or time objects. 
    """
    
    @classmethod
    def from_data(cls, value: datetime | time) -> str:
        """
        Method to convert `value` to string for serialization.
        """
        instance_type = "d" if isinstance(value, datetime) else "t"

        return f"{instance_type}:{value.isoformat()}"
    
    @classmethod
    def to_data(cls, value: str, reference: BaseFile) -> datetime | time:
        """
        Method to reverse the conversion at `from_data`.
        """
        instance_type, data = value.split(":", maxsplit=1)

        data_type = datetime if instance_type == "d" else time
        return data_type.fromisoformat(data)


class TransmuterAttribute(Transmuter):
    """
    Transmuter class to handle attribute that are objects from classes. 
    """
    
    @classmethod
    def from_data(cls, value: object) -> dict[str, Any]:
        """
        Method to convert `value` to dict for serialization.
        """
        values = value.__serialize__

        if 'related_file_object' in values:
            values['related_file_object'] = values['related_file_object'].id

        return {
            "__source__": TransmuterObjectClass.from_data(value),
            "values": values
        }

    @classmethod
    def to_data(cls, value: dict[str, Any], reference: BaseFile) -> object:
        """
        Method to reverse the conversion at `from_data`.
        """
        attribute_object = TransmuterClass.to_data(value["__source__"], reference=reference)
        
        values = value["values"]

        if 'related_file_object' in values:
            values['related_file_object'] = reference

        return attribute_object(**values)
    

class TransmuterValue(Transmuter):
    """
    Transmuter class to handle attributes that don`t need to be converted. 
    """
    
    @classmethod
    def from_data(cls, value: Any) -> Any:
        """
        Method to return the same `value` for serialization.
        """
        return value
    
    @classmethod
    def to_data(cls, value: Any, reference: BaseFile) -> Any:
        """
        Method to reverse the conversion at `from_data`.
        """
        return value
    

class TransmuterThumbnail(Transmuter):
    """
    Transmuter class to handle the FileThumbnail object. 
    """
    
    @classmethod
    def from_data(cls, value: FileThumbnail) -> dict[str, Any]:
        """
        Method to convert `value` to dict for serialization.
        """
        thumbnail = value.__serialize__

        # Convert _static_file and _animated_file to Base64
        # static_file = thumbnail["_static_file"].content_as_base64 if thumbnail["_static_file"] else None
        # animated_file = thumbnail["_animated_file"].content_as_base64 if thumbnail["_animated_file"] else None
        # TODO: Simplify usage of serializer instead of whole file to save only the content as base64.
        static_file = FileWithContentDictionarySerializer.serialize(thumbnail["_static_file"]) if thumbnail["_static_file"] else None
        animated_file = FileWithContentDictionarySerializer.serialize(thumbnail["_animated_file"]) if thumbnail["_animated_file"] else None
        
        return {
            "static_defaults": TransmuterClass.from_data(thumbnail["static_defaults"]),
            "animated_defaults": TransmuterClass.from_data(thumbnail["animated_defaults"]),
            "static_file": static_file,
            "animated_file": animated_file,
            "image_engine": TransmuterClass.from_data(thumbnail["image_engine"]),
            "video_engine": TransmuterClass.from_data(thumbnail["video_engine"]),
            "render_static_pipeline": TransmuterPipeline.from_data(thumbnail["render_static_pipeline"]),
            "render_animated_pipeline": TransmuterPipeline.from_data(thumbnail["render_animated_pipeline"])
        }

    @classmethod
    def to_data(cls, value: dict[str, Any], reference: BaseFile) -> FileThumbnail:
        """
        Method to reverse the conversion at `from_data`.
        """
        file_thumbnail = FileThumbnail()
        file_thumbnail.related_file_object = reference

        file_thumbnail.static_defaults = TransmuterClass.to_data(value["static_defaults"], reference=reference)
        file_thumbnail.animated_defaults = TransmuterClass.to_data(value["animated_defaults"], reference=reference)
        file_thumbnail.image_engine = TransmuterClass.to_data(value["image_engine"], reference=reference)
        file_thumbnail.video_engine = TransmuterClass.to_data(value["video_engine"], reference=reference)
        file_thumbnail.render_static_pipeline = TransmuterPipeline.to_data(value["render_static_pipeline"], reference=reference)
        file_thumbnail.render_animated_pipeline = TransmuterPipeline.to_data(value["render_animated_pipeline"], reference=reference)

        if value["static_file"]:
            file_thumbnail._static_file = FileWithContentDictionarySerializer.deserialize(value["static_file"])
            # file_thumbnail._static_file = thumbnail["_static_file"].content_as_base64 if thumbnail["_static_file"] else None
        
        if value["animated_file"]:
            file_thumbnail._animated_file = FileWithContentDictionarySerializer.deserialize(value["animated_file"])
            # file_thumbnail._animated_file = thumbnail["_animated_file"].content_as_base64 if thumbnail["_animated_file"] else None

        return file_thumbnail


class TransmuterHashes(Transmuter):
    """
    Transmuter class to handle the FileHash object. 
    """
    
    @classmethod
    def from_data(cls, value: FileHashes) -> dict[str, Any]:       
        """
        Method to convert `value` to dict for serialization.
        """
        hashes = value.__serialize__

        cache = {}
        for hash_name, hash_tuple in hashes['_cache']:
            cache[hash_name] = (
                hash_tuple[0], cls.serializer.serialize(hash_tuple[1]), TransmuterClass.from_data(hash_tuple[2])
            )

        # We don`t need `_loaded` neither `related_file_object` as they can be inferred from _cache and file object.
        return cache
    
    @classmethod
    def to_data(cls, value: dict[str, Any], reference: BaseFile) -> FileHashes:
        """
        Method to reverse the conversion at `from_data`.
        """
        file_hashes = FileHashes()
        file_hashes.related_file_object = reference

        for hash_name, hash_tuple in value.items():
            file_hashes[hash_name] = (hash_tuple[0], cls.serializer.deserialize(hash_tuple[1]), TransmuterClass.to_data(hash_tuple[2], reference=reference))

        return file_hashes


class TransmuterContentFiles(Transmuter):
    """
    Transmuter class to handle the FilePacket object. 
    """
    
    @classmethod
    def from_data(cls, value: FilePacket) -> dict[str, Any]:
        """
        Method to convert `value` to dict for serialization.
        The history attribute of FilePacket will not be serialized. 
        """
        # Case should cache convert to base64
        content_files = value.__serialize__

        return {
            "internal_files": {
                key: cls.serializer.serialize(value)
                for key, value in content_files["_internal_files"].items()
            },
            "unpack_data_pipeline": TransmuterPipeline.from_data(content_files["unpack_data_pipeline"]),
        }
    
    @classmethod
    def to_data(cls, value: dict[str, Any], reference: BaseFile) -> FilePacket:
        """
        Method to reverse the conversion at `from_data`.
        """
        return FilePacket(
            _internal_files={
                key: cls.serializer.deserialize(value)
                for key, value in value["internal_files"]
            },
            unpack_data_pipeline=TransmuterPipeline.to_data(value["unpack_data_pipeline"], reference=reference)
        )


class TransmuterContent(Transmuter):
    """
    Transmuter class to handle the FileTContent object. 
    """
    
    @classmethod
    def from_data(cls, value: FileContent) -> dict[str, Any]:
        """
        Method to convert `value` to dict for serialization.
        """
        dict_to_return = value.__serialize__

        if value.should_load_to_memory:
            raise SerializerError("Content for file should be serialized as it should be load to memory and may not be available later.\nPlease, use a serializer that saves the content.")

        del dict_to_return["_cached_content"]
        del dict_to_return['related_file_object']

        # Convert buffer to a structure that can be used to instantiate a new buffer later.
        dict_to_return["buffer"] = f"{getattr(dict_to_return['buffer'], 'name', '')}:{getattr(dict_to_return['buffer'], 'mode', '')}"

        return dict_to_return
    
    @classmethod
    def to_data(cls, value: dict[str, Any], reference: BaseFile) -> FileContent:
        """
        Method to reverse the conversion at `from_data`.
        """
        buffer = value.pop("buffer").rsplit(':', 1)
        
        return FileContent(
            raw_value=None,
            related_file_object=reference,
            buffer=reference.storage.open_file(path=buffer[0], mode=buffer[1]),
            **value
        )


class TransmuterContentBase64(Transmuter):
    """
    Transmuter class to handle the FileContent object as its base64 representation. 
    """
    
    @classmethod
    def from_data(cls, value: FileContent) -> str:
        """
        Method to convert `value` to string for serialization.
        """
        dict_to_return = value.__serialize__

        del dict_to_return["_cached_content"]
        del dict_to_return['related_file_object']

        dict_to_return["content_base64"] = value.content_as_base64

        # Convert buffer to a structure that can be used to instantiate a new buffer later.
        dict_to_return["buffer"] = f"{getattr(dict_to_return['buffer'], 'name', '')}:{getattr(dict_to_return['buffer'], 'mode', '')}"

        return dict_to_return

    @classmethod
    def to_data(cls, value: dict[str, Any], reference: BaseFile) -> FileContent:
        """
        Method to reverse the conversion at `from_data`.
        """
        buffer = value.pop("buffer").rsplit(':', 1)
        content = b64decode(value.pop("content_base64"))
        
        return FileContent(
            related_file_object=reference,
            buffer=reference.storage.open_file(path=buffer[0], mode=buffer[1]),
            _cached_content=content,
            **value
        )
    

class SerializerJsonMixin:
    """
    Class helper to convert a serialization class to serialize/deserialize JSON.
    """

    @classmethod
    def serialize(cls, source: BaseFile) -> str:
        """
        Method to serialize the input `source` as a JSON string.
        """
        from json import dumps
        dict_to_convert = super().serialize(source=source)

        return dumps(dict_to_convert)

    @classmethod
    def deserialize(cls, source: str) -> BaseFile:
        """
        Method to deserialize the JSON string input `source`.
        """
        from json import loads

        dict_to_parse = loads(source)

        return super().deserialize(source=dict_to_parse)


class FileDictionarySerializer:
    """
    Class that allow handling of Serialization/Deserialization from BaseFile instance to and from a Python dictionary.
    This class was created with specificity in mind and would need to be override if the object to be serialized is
    has a custom class based on BaseFile.
    The content attribute will not be serialized.
    """

    # Datetime serializer/deserializer
    create_date = TransmuterDatetime()
    update_date = TransmuterDatetime()

    # Class serializer/deserializer
    storage=TransmuterClass()
    serializer=TransmuterClass()
    uri_handler=TransmuterClass()
    mime_type_handler=TransmuterObjectClass()

    # Pipelines serializer/deserializer
    extract_data_pipeline = TransmuterPipeline()
    compare_pipeline = TransmuterPipeline()
    hasher_pipeline = TransmuterPipeline()
    rename_pipeline = TransmuterPipeline()
    compare_pipeline = TransmuterPipeline()

    # File Control classes serializer/deserializer
    _option = TransmuterAttribute()
    _actions = TransmuterAttribute()
    _naming = TransmuterAttribute()
    _state = TransmuterAttribute()
    _meta = TransmuterAttribute()
    _content_files = TransmuterContentFiles()
    _thumbnail = TransmuterThumbnail()
    hashes = TransmuterHashes()
    _content = TransmuterContent()

    # Raw attribute serializer/deserilizer
    id = TransmuterValue()
    filename = TransmuterValue()
    extension = TransmuterValue()
    _path = TransmuterValue()
    _save_to = TransmuterValue()
    relative_path = TransmuterValue()
    length = TransmuterValue()
    mime_type = TransmuterValue()
    type = TransmuterValue()
    _pipelines_override_keyword_arguments = TransmuterValue()
    __version__ = TransmuterValue()

    @classmethod
    def serialize(cls, source: BaseFile) -> dict[str, str | int | bool]:
        """
        Method to serialize the input `source` 
        """
        return {
            "__source__": TransmuterClass.from_data(source.__class__),
            **{
                attribute: getattr(cls, attribute).from_data(value=getattr(source, attribute))
                for attribute in cls.transmuters
                if hasattr(source, attribute)
            }
        }

    @classmethod
    def deserialize(cls, source: dict[str, Any]) -> BaseFile:
        """
        Method to deserialize the input `source` 
        """
        data = source.copy()

        class_instance = TransmuterClass.to_data(data["__source__"], reference=None)
        # Create empty file
        file_object = class_instance.__new__(class_instance)
        
        # Process storage before anything else
        file_object.storage = cls.storage.to_data(data["storage"], reference=file_object)

        # Fill content of file with deserialized objects
        kwargs = {
            attribute: getattr(cls, attribute).to_data(value=data[attribute], reference=file_object)
            for attribute in cls.transmuters
        }

        file_object.__init__(**kwargs)

        return file_object


class FileWithContentDictionarySerializer(FileDictionarySerializer):
    """
    Class that allow handling of Serialization/Deserialization from BaseFile instance to and from a Python dictionary.
    This class was created with specificity in mind and would need to be override if the object to be serialized is
    has a custom class based on BaseFile.
    The content attribute will be serialized. 
    """
    
    _content = TransmuterContentBase64()


class FileJsonSerializer(SerializerJsonMixin, FileDictionarySerializer):
    """
    Class that allow handling of Serialization/Deserialization from BaseFile instance to and from a json string.
    This class was created with specificity in mind and would need to be override if the object to be serialized is
    has a custom class based on BaseFile.
    The content attribute will not be serialized.
    """


class FileWithContentJsonSerializer(SerializerJsonMixin, FileWithContentDictionarySerializer):
    """
    Class that allow handling of Serialization/Deserialization from BaseFile instance to and from a json string.
    This class was created with specificity in mind and would need to be override if the object to be serialized is
    has a custom class based on BaseFile.
    The content attribute will be serialized. 
    """
