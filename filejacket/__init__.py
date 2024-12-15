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

from .exception import (
    ImproperlyConfiguredFile,
    NoInternalContentError,
    OperationNotAllowed,
    ReservedFilenameError,
    ValidationError,
)
from .file import BaseFile
from .handler import System, URI

# Module with engines for adapters
from .engines.storage import StorageEngine
from .engines.image import ImageEngine
from .engines.video import VideoEngine

# Module with classes adapted from engines
from .adapters.mimetype import LibraryMimeTyper, APIMimeTyper
from .adapters.image import OpenCVImage, PillowImage, WandImage
from .adapters.video import MoviePyVideo
from .adapters.storage import WindowsFileSystem, LinuxFileSystem

# Module with classes that define the pipelines and its processors classes.
# A Pipeline is a sequence that loop processors to be run.
from .pipelines import Processor, Pipeline

# Module with base classes for pipeline classes.
from .pipelines.base import (
    BaseComparer,
    BaseExtractor,
    BaseHasher,
    BaseRenamer,
    BaseRender,
)

# Module with pipeline classes for comparing Files.
from .pipelines.comparer import (
    BinaryCompare,
    DataCompare,
    HashCompare,
    LousyNameCompare,
    MimeTypeCompare,
    NameCompare,
    SizeCompare,
    TypeCompare,
)

# Module with pipeline classes for extracting data for files from multiple sources.
from .pipelines.extractor import (
    PackageExtractor,
    FileSystemDataExtractor,
    FilenameAndExtensionFromPathExtractor,
    MimeTypeFromFilenameExtractor,
    HashFileExtractor,
    FilenameFromURLExtractor,
    PathFromURLExtractor,
    FilenameFromMetadataExtractor,
    MetadataExtractor,
    SevenZipCompressedFilesFromPackageExtractor,
    AudioMetadataFromContentExtractor,
    RarCompressedFilesFromPackageExtractor,
    ZipCompressedFilesFromPackageExtractor,
    MimeTypeFromContentExtractor,
)

# Module with pipeline classes for generating or extracting hashed data related to file.
from .pipelines.hasher import CRC32Hasher, MD5Hasher, SHA256Hasher

# Module with pipeline classes for renaming files.
from .pipelines.renamer import WindowsRenamer, LinuxRenamer, UniqueRenamer

# module with pipeline classes for render content representation.
from .pipelines.render import (
    BaseAnimatedRender,
    BaseStaticRender,
    DocumentFirstPageRender,
    ImageAnimatedRender,
    ImageRender,
    PSDRender,
    StaticAnimatedRender,
    VideoRender,
)

# Module with classes for serializing/deserializing objects.
from .serializer import PickleSerializer, JSONSerializer, FileJsonSerializer


__all__ = [
    "APIMimeTyper",
    "AudioMetadataFromContentExtractor",
    "BaseFile",
    "BinaryCompare",
    "BaseComparer",
    "PackageExtractor",
    "ContentFile",
    "CRC32Hasher",
    "DataCompare",
    "BaseExtractor",
    "File",
    "FileSystemDataExtractor",
    "FilenameAndExtensionFromPathExtractor",
    "FilenameFromMetadataExtractor",
    "FilenameFromURLExtractor",
    "HashCompare",
    "HashFileExtractor",
    "BaseHasher",
    "ImageEngine",
    "ImproperlyConfiguredFile",
    "JSONSerializer",
    "LibraryMimeTyper",
    "LinuxFileSystem",
    "LinuxRenamer",
    "LousyNameCompare",
    "MD5Hasher",
    "MetadataExtractor",
    "MimeTypeCompare",
    "MimeTypeFromContentExtractor",
    "MimeTypeFromFilenameExtractor",
    "NameCompare",
    "NoInternalContentError",
    "OpenCVImage",
    "OperationNotAllowed",
    "PathFromURLExtractor",
    "PickleSerializer",
    "PillowImage",
    "Pipeline",
    "Processor",
    "RarCompressedFilesFromPackageExtractor",
    "BaseRenamer",
    "BaseRender",
    "BaseAnimatedRender",
    "BaseStaticRender",
    "DocumentFirstPageRender",
    "ImageAnimatedRender",
    "ImageRender",
    "PSDRender",
    "StaticAnimatedRender",
    "VideoRender",
    "ReservedFilenameError",
    "SHA256Hasher",
    "SevenZipCompressedFilesFromPackageExtractor",
    "SizeCompare",
    "StorageEngine",
    "StreamFile",
    "System",
    "TypeCompare",
    "URI",
    "UniqueRenamer",
    "ValidationError",
    "MoviePyVideo",
    "WandImage",
    "WindowsFileSystem",
    "WindowsRenamer",
    "ZipCompressedFilesFromPackageExtractor",
    "VideoEngine",
    "FileJsonSerializer",
]


class ContentFile(BaseFile):
    """
    Class to create a file from an in memory content.
    It can load a file already saved as BaseFile allow it, but is recommended to use `File` instead
    because it will have a more complete pipeline for data extraction.
    a new one from memory using `ContentFile`.
    """

    extract_data_pipeline: Pipeline = Pipeline(
        "filejacket.pipelines.extractor.FilenameFromMetadataExtractor",
        "filejacket.pipelines.extractor.MimeTypeFromFilenameExtractor",
        "filejacket.pipelines.extractor.MimeTypeFromContentExtractor",
    )
    """
    Pipeline to extract data from multiple sources.
    """


class StreamFile(BaseFile):
    """
    Class to create a file from an HTTP stream that has a header with metadata.
    """

    extract_data_pipeline: Pipeline = Pipeline(
        "filejacket.pipelines.extractor.FilenameFromMetadataExtractor",
        "filejacket.pipelines.extractor.FilenameFromURLExtractor",
        "filejacket.pipelines.extractor.MimeTypeFromFilenameExtractor",
        "filejacket.pipelines.extractor.MimeTypeFromContentExtractor",
        "filejacket.pipelines.extractor.MetadataExtractor",
    )
    """
    Pipeline to extract data from multiple sources.
    """


class File(BaseFile):
    """
    Class to create a file from an already saved path in filesystem.
    It can create a new file as BaseFile allow it, but is recommended to create
    a new one from memory using `ContentFile`.
    """

    extract_data_pipeline: Pipeline = Pipeline(
        "filejacket.pipelines.extractor.FilenameAndExtensionFromPathExtractor",
        "filejacket.pipelines.extractor.MimeTypeFromFilenameExtractor",
        "filejacket.pipelines.extractor.FileSystemDataExtractor",
        "filejacket.pipelines.extractor.HashFileExtractor",
    )
    """
    Pipeline to extract data from multiple sources.
    """
