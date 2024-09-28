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
from .adapters.mimetype import LibraryMimeTyper, APIMimeTyper
# Module with classes that define the pipelines and its processors classes.
# A Pipeline is a sequence that loop processors to be run.
from .pipelines import Processor, Pipeline
# Module with pipeline classes for comparing Files.
from .pipelines.comparer import (
    BaseComparer,
    BinaryCompare,
    DataCompare,
    HashCompare,
    LousyNameCompare,
    MimeTypeCompare,
    NameCompare,
    SizeCompare,
    TypeCompare
)
# Module with pipeline classes for extracting data for files from multiple sources.
from .pipelines.extractor import (
    Extractor,
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
    MimeTypeFromContentExtractor
)
# Module with pipeline classes for generating or extracting hashed data related to file.
from .pipelines.hasher import BaseHasher, CRC32Hasher, MD5Hasher, SHA256Hasher
# Module with pipeline classes for renaming files.
from .pipelines.renamer import BaseRenamer, WindowsRenamer, LinuxRenamer, UniqueRenamer
# Module with classes for serializing/deserializing objects.
from .serializer import PickleSerializer, JSONSerializer
from .engines.storage import StorageEngine
from .adapters.storage import WindowsFileSystem, LinuxFileSystem

__all__ = [
    'APIMimeTyper', 'AudioMetadataFromContentExtractor', 'BaseFile', 'BinaryCompare',
    'BaseComparer', 'PackageExtractor', 'ContentFile', 'CRC32Hasher', 'DataCompare',
    'Extractor', 'File', 'FileSystemDataExtractor', 'FilenameAndExtensionFromPathExtractor',
    'FilenameFromMetadataExtractor', 'FilenameFromURLExtractor', 'HashCompare', 'HashFileExtractor',
    'BaseHasher', 'ImageEngine', 'ImproperlyConfiguredFile', 'JSONSerializer', 'LibraryMimeTyper',
    'LinuxFileSystem',  'LinuxRenamer', 'LousyNameCompare', 'MD5Hasher',
    'MetadataExtractor', 'MimeTypeCompare', 'MimeTypeFromContentExtractor',
    'MimeTypeFromFilenameExtractor', 'NameCompare', 'NoInternalContentError', 'OpenCVImage',
    'OperationNotAllowed', 'PathFromURLExtractor', 'PickleSerializer', 'PillowImage', 'Pipeline',
    'Processor', 'RarCompressedFilesFromPackageExtractor', 'BaseRenamer', 'ReservedFilenameError',
    'SHA256Hasher', 'SevenZipCompressedFilesFromPackageExtractor',
    'SizeCompare', 'StorageEngine', 'StreamFile', 'System', 'TypeCompare', 'URI', 'UniqueRenamer',
    'ValidationError', 'WandImage', 'WindowsFileSystem', 'WindowsRenamer',
    'ZipCompressedFilesFromPackageExtractor',
]


class ContentFile(BaseFile):
    """
    Class to create a file from an in memory content.
    It can load a file already saved as BaseFile allow it, but is recommended to use `File` instead
    because it will have a more complete pipeline for data extraction.
    a new one from memory using `ContentFile`.
    """

    extract_data_pipeline: Pipeline = Pipeline(
        'filejacket.pipelines.extractor.FilenameFromMetadataExtractor',
        'filejacket.pipelines.extractor.MimeTypeFromFilenameExtractor',
        'filejacket.pipelines.extractor.MimeTypeFromContentExtractor',
    )
    """
    Pipeline to extract data from multiple sources.
    """


class StreamFile(BaseFile):
    """
    Class to create a file from an HTTP stream that has a header with metadata.
    """

    extract_data_pipeline: Pipeline = Pipeline(
        'filejacket.pipelines.extractor.FilenameFromMetadataExtractor',
        'filejacket.pipelines.extractor.FilenameFromURLExtractor',
        'filejacket.pipelines.extractor.MimeTypeFromFilenameExtractor',
        'filejacket.pipelines.extractor.MimeTypeFromContentExtractor',
        'filejacket.pipelines.extractor.MetadataExtractor'
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
        'filejacket.pipelines.extractor.FilenameAndExtensionFromPathExtractor',
        'filejacket.pipelines.extractor.MimeTypeFromFilenameExtractor',
        'filejacket.pipelines.extractor.FileSystemDataExtractor',
        'filejacket.pipelines.extractor.HashFileExtractor',
    )
    """
    Pipeline to extract data from multiple sources.
    """
