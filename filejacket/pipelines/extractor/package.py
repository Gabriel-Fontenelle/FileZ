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

from datetime import datetime
from io import IOBase, BytesIO
from sys import getsizeof
from tarfile import TarFile, TarError
from typing import Any, TYPE_CHECKING, Type, IO
from zipfile import BadZipFile, ZipFile

from rarfile import BadRarFile, RarFile, NotRarFile

from ..base import BaseExtractor
from .. import Pipeline
from ..hasher import CRC32Hasher
from ...exception import ValidationError
from ...utils import LazyImportClass

if TYPE_CHECKING:
    from ...file import BaseFile
    from ...engines.storage import StorageEngine
    from psd_tools import PSDImage
    from py7zr import SevenZipFile, FileInfo

__all__ = [
    "PackageExtractor",
    "PSDLayersFromPackageExtractor",
    "SevenZipCompressedFilesFromPackageExtractor",
    "RarCompressedFilesFromPackageExtractor",
    "TarCompressedFilesFromPackageExtractor",
    "ZipCompressedFilesFromPackageExtractor",
]


class PackageExtractor(BaseExtractor):
    """
    Extractor class with focus to processing information from file's content.
    This class was created to allow parsing and extraction of data designated to
    internal files.
    """

    extensions: set[str]
    extensions = None
    """
    Attribute to store allowed extensions for use in `validator`.
    This attribute should be override in children classes.
    """
    compressor_class: Type[type]
    compressor_class = None
    """
    Attribute to store the current class of compressor for use in `content_buffer` and `decompress` methods.
    This attribute should be override in children classes.
    """
    stopper: bool = True
    """
    Variable that define if this class used as processor should stop the pipeline.
    """

    class ContentBuffer(IOBase):
        """
        Class to allow consumption of buffer in a lazy way.
        This class should be override in children of PackageExtractor to
        implementation of method read().
        """

        source_file_object: BaseFile
        source_file_object = None
        """
        Attribute to store the related file object that has the buffer for the compressed content.
        """
        compressor: Type[type]
        compressor = None
        """
        Attribute to store the class of the compressor able to uncompress the content.  
        """
        compressed_object: Any
        compressed_object = None
        """
        Attribute to store the instance of the compressor.
        """
        filename: str
        filename = None
        """
        Attribute to store the name of file that should be extract for this content.
        """
        mode: str
        mode = None
        """
        Attribute to store the mode of read for the uncompressed content. 
        """

        reference_class: Type[PackageExtractor]
        reference_class = None
        """
        Attribute to allow serialization of this  class as local class.
        """

        buffer: Any
        """
        Attribute to store the current initialized buffer.
        """

        def __init__(
            self: PackageExtractor.ContentBuffer,
            source_file_object: BaseFile,
            compressor_class: Type[type],
            internal_file_filename: str,
            mode: str,
            reference: Type[PackageExtractor],
        ) -> None:
            """
            Method to initiate the object saving the data required to allow decompressing and reading content
            for specific file.
            """
            self.source_file_object = source_file_object
            self.compressor = compressor_class
            self.filename = internal_file_filename
            self.mode = mode
            self.reference = reference

        def read(
            self: PackageExtractor.ContentBuffer, *args: Any, **kwargs: Any
        ) -> str | bytes:
            """
            Method to read the content of the object initiating the buffer if not exists.
            """
            if not hasattr(self, "buffer"):
                # Instantiate the buffer of inner content
                self.mount_buffer()

            return self.buffer.read(*args, **kwargs)

        def mount_buffer(self: PackageExtractor.ContentBuffer) -> None:
            """
            Method to initiate the buffer object if not exists.
            This method should be overwritten in child class.
            """
            raise NotImplementedError(
                f"Method mount_buffer of PackageExtractor.ContentBuffer should be override in child class "
                f"{self.__class__.__name__}."
            )

        def seek(self, *args: Any, **kwargs: Any) -> int:
            """
            Method to seek the content in the buffer.
            Buffer must exist for this method to work, else no action will be taken.
            """
            if not hasattr(self, "buffer"):
                # Initiate the buffer
                # It will begin extraction of file to have access to its buffer.
                self.mount_buffer()

            return self.buffer.seek(*args, **kwargs)

        def seekable(self) -> bool:
            """
            Method to verify if buffer is seekable.
            Buffer must exist for this method to work, else no action will be taken.
            
            For better performance this method should be override in child class to avoid using buffer, as it extract the content
            in memory.
            """
            if not hasattr(self, "buffer"):
                # Initiate the buffer
                # It will begin extraction of file to have access to its buffer.
                self.mount_buffer()

            return self.buffer.seekable()

        def close(self) -> None:
            """
            Method to close the buffer.
            Buffer must exist for this method to work, else no action will be taken.
            """
            if not hasattr(self, "buffer"):
                return

            self.buffer.close()
            delattr(self, "buffer")

    @classmethod
    def validate(cls, file_object: BaseFile) -> None:
        """
        Method to validate if content can be extract to given extension.
        """
        if cls.extensions is None:
            raise NotImplementedError(
                f"The attribute `extensions` is not overwritten in child class {cls.__name__}"
            )

        if cls.compressor_class is None:
            raise NotImplementedError(
                f"The attribute `compressor_class` is not overwritten in child class {cls.__name__}"
            )

        # The ValidationError should be captured in children classes else it will not register as an error and
        # the pipeline will break.
        if file_object.extension not in cls.extensions:
            raise ValidationError(
                f"Extension `{file_object.extension}` not allowed in validate for class {cls.__name__}"
            )

    @classmethod
    def decompress(cls, file_object: BaseFile, overrider: bool, **kwargs: Any) -> bool:
        """
        Method to uncompress the content from a file_object.
        This method must be override in child class.
        """
        raise NotImplementedError(
            "Method extract_content must be overwritten on child class."
        )

    @classmethod
    def content_buffer(
        cls, file_object: BaseFile, internal_file_name: str, mode: str = "rb"
    ) -> ContentBuffer:
        """
        Method to create a buffer pointing to the uncompressed content.
        This method must work lazily, extracting the content only when the buffer is read.
        This method must be override in child class.
        """
        raise NotImplementedError(
            "Method content_buffer must be overwritten on child class."
        )

    @classmethod
    def process(cls, **kwargs: Any) -> bool:
        """
        Method used to run this class on Processor`s Pipeline for Extracting info from Data.
        This process method is created exclusively to pipeline for objects inherent from BaseFile.

        The processor for package extraction override the method `BaseExtractor.process` in order to validate
        the extension before processing the `object_to_process`.
        """
        try:
            object_to_process: BaseFile = kwargs["object_to_process"]
            cls.validate(file_object=object_to_process)
        except (ValidationError, KeyError):
            return False

        return super().process(**kwargs)


class MastrokaFilesFromPackageExtractor(PackageExtractor):
    """
    Class to extract internal files from mka, mkv files.
    """


class PSDLayersFromPackageExtractor(PackageExtractor):
    """
    Class to extract internal files from PSD files.
    """

    extensions: set[str] = {"psd", "psb"}
    """
    Attribute to store allowed extensions for use in `validator`.
    """
    compressor_class: Type[PSDImage] = LazyImportClass("PSDImage", "psd_tools")
    """
    Attribute to store the current class of compressor for use in `content_buffer` and `decompress` methods.
    """

    @classmethod
    def content_buffer(
        cls, file_object: BaseFile, internal_file_name: str, mode: str = "rb"
    ) -> PackageExtractor.ContentBuffer:
        """
        Method to create a buffer pointing to the uncompressed content.
        This method must work lazily, extracting the content only when the buffer is read.
        """

        class PSDContentBuffer(PackageExtractor.ContentBuffer):
            """
            Class to allow consumption of buffer in a lazy way.
            """

            def mount_buffer(self: PackageExtractor.ContentBuffer) -> None:
                """
                Method to initiate the buffer object if not exists.
                """
                compressed: IO = self.compressor.open(
                    fp=self.source_file_object.content_as_buffer
                )

                self.buffer: BytesIO = BytesIO()

                # Save PSD content for layer in buffer.
                compressed[self.filename].save(fp=self.buffer)

                # Reset buffer to allow read.
                self.buffer.seek(0)
                
            def seekable(self) -> bool:
                """
                Method to verify if buffer is seekable.
                This method override the default behavior for better performance to avoid extracting the self.filename.
                
                Because the layer must be extracted to a auxiliary buffer it will always be seekable.
                """                
                return True

        return PSDContentBuffer(
            file_object, cls.compressor_class, internal_file_name, mode, cls
        )

    @classmethod
    def decompress(cls, file_object: BaseFile, overrider: bool, **kwargs: Any) -> bool:
        """
        Method to decompress the content from a file_object.
        """
        try:
            # We need to create the directory because there is no extractor for handling PSD.
            extraction_path: str = kwargs.pop("decompress_to")

            # We don't need to reset the buffer before calling it, because it will be reset
            # if already cached. The next time property buffer is called it will reset again.
            compressed_file: PSDImage = cls.compressor_class.open(
                fp=file_object.content_as_buffer
            )

            for index, internal_file in compressed_file:
                filename = f"{index}-{internal_file.name or internal_file.layer_id}.psd"

                path: str = file_object.storage.join(extraction_path, filename)
                if not file_object.storage.exists(path) or overrider:
                    # Create directory if not exists
                    file_object.storage.create_directory(extraction_path)

                    # Save content buffer for file
                    buffer: BytesIO = BytesIO()
                    internal_file.save(fp=buffer)

                    # Reset pointer to initial point.
                    buffer.seek(0)

                    # Save buffer
                    file_object.storage.save_file(
                        path=path, content=buffer, file_mode="w", write_mode="b"
                    )

        except (OSError, ValueError):
            return False

        return True

    @classmethod
    def extract(cls, file_object: BaseFile, overrider: bool, **kwargs: Any) -> bool:
        """
        Method to extract the information necessary from a file_object.
        """
        if not file_object.save_to:
            return False

        try:
            file_system: Type[StorageEngine] = file_object.storage
            file_class: Type[BaseFile] = file_object.__class__

            # We don't need to reset the buffer before calling it, because it will be reset
            # if already cached. The next time property buffer is called it will reset again.
            compressed_object: PSDImage = cls.compressor_class.open(
                fp=file_object.content_as_buffer
            )

            for index, internal_file in enumerate(compressed_object):
                filename: str = (
                    f"{index}-{internal_file.name or internal_file.layer_id}.psd"
                )

                # Skip duplicate only if not choosing to override.
                if filename in file_object._content_files and not overrider:
                    continue

                # Create file object for internal file
                internal_file_object = file_class(
                    path=file_system.join(
                        file_object.save_to, file_object.filename, filename
                    ),
                    extract_data_pipeline=Pipeline(
                        "filejacket.pipelines.extractor.FilenameAndExtensionFromPathExtractor",
                        "filejacket.pipelines.extractor.MimeTypeFromFilenameExtractor",
                    ),
                    file_system_handler=file_system,
                )

                # Update size of file
                internal_file_object.length = getsizeof(internal_file.tobytes())

                # Set up action to be extracted instead of to save.
                internal_file_object._actions.to_extract()

                # Set mode
                mode: str = "rb"

                # Set up content pointer to internal file using content_buffer
                internal_file_object.content_as_buffer = cls.content_buffer(
                    file_object=file_object, internal_file_name=filename, mode=mode
                )

                # Set up metadata for internal file
                internal_file_object.meta.hashable = False
                internal_file_object.meta.internal = True

                # Add internal file as File object to file.
                file_object._content_files[filename] = internal_file_object

            # Update metadata and actions.
            file_object.meta.packed = True
            file_object._actions.listed()

        except OSError:
            return False

        return True


class TarCompressedFilesFromPackageExtractor(PackageExtractor):
    """
    Class to extract internal files from tar.gz or tar.bz files.
    As gzip and bzip compression don`t provide a manifest, as it is not an archive format just a compression algorithm,
    the tarfile library should be used to try to extract information of files with compression .bz and .gz as its the
    most common usage of tar with those compressors.
    """

    extensions: set[str] = {"gz", "tar", "bz", "cbt"}
    """
    Attribute to store allowed extensions for use in `validator`.
    """
    compressor_class: Type[TarFile] = TarFile
    """
    Attribute to store the current class of compressor for use in `content_buffer` and `decompress` methods.
    """

    @classmethod
    def content_buffer(
        cls, file_object: BaseFile, internal_file_name: str, mode: str = "rb"
    ) -> PackageExtractor.ContentBuffer:
        """
        Method to create a buffer pointing to the uncompressed content.
        This method must work lazily, extracting the content only when the buffer is read.
        """

        class TarContentBuffer(PackageExtractor.ContentBuffer):
            """
            Class to allow consumption of buffer in a lazy way.
            """

            def mount_compressed_object(self: PackageExtractor.ContentBuffer) -> None:
                """
                Method to initialize the compressed file from the upstream package buffer.
                """
                # Instantiate the buffer of inner content
                self.compressed_object: TarFile = self.compressor(
                    fileobj=self.source_file_object.content_as_buffer
                )
                
            def mount_buffer(self: PackageExtractor.ContentBuffer) -> None:
                """
                Method to initiate the buffer object if not exists.
                """
                if not self.compressed_object:
                    self.mount_compressed_object()
                
                content = self.compressed_object.extractfile(member=self.filename)

                if content is None:
                    self.buffer = BytesIO(b"")
                else:
                    self.buffer = content

            def read(self, *args: Any, **kwargs: Any) -> bytes:
                """
                Method to read the content of the object initiating the buffer if not exists.
                """
                if not hasattr(self, "buffer"):
                    # Instantiate the buffer of inner content
                    self.mount_buffer()

                return self.buffer.read(*args, **kwargs)

            def seekable(self) -> bool:
                """
                Method to verify if buffer is seekable.
                This method override the default behavior for better performance to avoid extracting the self.filename.
                """                
                if not self.compressed_object:
                    self.mount_compressed_object()
                
                # The fileobj is the same object as the self.source_file_object.content_as_buffer 
                # used in mount_compressed_object.
                return self.compressed_object.fileobj.seekable()
            
        return TarContentBuffer(
            file_object, cls.compressor_class, internal_file_name, mode, cls
        )

    @classmethod
    def decompress(cls, file_object: BaseFile, overrider: bool, **kwargs: Any) -> bool:
        """
        Method to uncompress the content from a file_object.
        """
        try:
            # We don't need to create the directory because the extractor will create it if not exists.
            extraction_path: str = kwargs.pop("decompress_to")

            # We don't need to reset the buffer before calling it, because it will be reset
            # if already cached. The next time property buffer is called it will reset again.
            with cls.compressor_class(
                fileobj=file_object.content_as_buffer
            ) as compressed_file:  # type: ignore
                # targets as None will extract all data, overwriting existing ones.
                targets: list | None = None

                if not overrider:
                    targets = []
                    for filename in compressed_file.getnames():
                        # Avoid files beginning with `..` or `/` for security reason.
                        if filename[0] == "/" or filename[0:2] == "..":
                            continue

                        if not file_object.storage.exists(
                            file_object.storage.join(extraction_path, filename)
                        ):
                            targets.append(filename)

                    # Avoid calling the extractor if the list is empty.
                    if not targets:
                        return True

                # Concurrent extract file in external file system using a custom pathlib.Path
                # with accessor informed by storage of file_object.
                compressed_file.extractall(
                    path=file_object.storage.get_pathlib_path(extraction_path),
                    members=targets,
                )

        except BadZipFile:
            return False

        return True

    @classmethod
    def extract(cls, file_object: BaseFile, overrider: bool, **kwargs: Any) -> bool:
        """
        Method to extract the information necessary from a file_object.
        """
        if not file_object.save_to:
            return False

        try:
            file_system: Type[StorageEngine] = file_object.storage
            file_class: Type[BaseFile] = file_object.__class__

            # We don't need to reset the buffer before calling it, because it will be reset
            # if already cached. The next time property buffer is called it will reset again.
            with cls.compressor_class(
                fileobj=file_object.content_as_buffer
            ) as compressed_object:  # type: ignore
                for internal_file in compressed_object.getmembers():
                    # Skip directories
                    if internal_file.isdir():
                        continue

                    # Skip inexisting filename if for some reason there is one.
                    if not internal_file.name:
                        continue

                    # Cast specifically created to fix a mypy error, as internal_file should always have a filename
                    filename: str = str(internal_file.name)

                    # Skip duplicate only if not choosing to override.
                    if filename in file_object._content_files and not overrider:
                        continue

                    # Create file object for internal file
                    internal_file_object = file_class(
                        path=file_system.join(file_object.save_to, filename),
                        extract_data_pipeline=Pipeline(
                            "filejacket.pipelines.extractor.FilenameAndExtensionFromPathExtractor",
                            "filejacket.pipelines.extractor.MimeTypeFromFilenameExtractor",
                        ),
                        file_system_handler=file_system,
                    )

                    # Update creation and modified date. As mtime is a integer in TarFile we should convert it to
                    # datetime.
                    internal_file_object.create_date = datetime.fromtimestamp(
                        internal_file.mtime
                    )
                    internal_file_object.update_date = datetime.fromtimestamp(
                        internal_file.mtime
                    )

                    # Update size of file
                    internal_file_object.length = internal_file.size

                    # Update hash generating the hash file and adding its content
                    if internal_file.chksum:
                        hash_file = CRC32Hasher.create_hash_file(
                            object_to_process=internal_file_object,
                            digested_hex_value=str(internal_file.chksum),
                        )
                        internal_file_object.hashes["crc32"] = (
                            str(internal_file.chksum),
                            hash_file,
                            CRC32Hasher,
                        )

                    # Set up action to be extracted instead of to save.
                    internal_file_object._actions.to_extract()

                    # Get mode from type
                    mode: str = "r" if internal_file_object.type == "text" else "rb"

                    # Set up content pointer to internal file using content_buffer
                    internal_file_object.content_as_buffer = cls.content_buffer(
                        file_object=file_object, internal_file_name=filename, mode=mode
                    )

                    # Set up metadata for internal file
                    internal_file_object.meta.hashable = False
                    internal_file_object.meta.internal = True

                    # Add internal file as File object to file.
                    file_object._content_files[filename] = internal_file_object

            # Update metadata and actions.
            file_object.meta.packed = True
            file_object._actions.listed()

        except TarError:
            return False

        return True


class ZipCompressedFilesFromPackageExtractor(PackageExtractor):
    """
    Class to extract internal files from zip and cbz files.
    """

    extensions: set[str] = {"zip", "cbz"}
    """
    Attribute to store allowed extensions for use in `validator`.
    """
    compressor_class: Type[ZipFile] = ZipFile
    """
    Attribute to store the current class of compressor for use in `content_buffer` and `decompress` methods.
    """

    @classmethod
    def content_buffer(cls, file_object, internal_file_name, mode="rb"):
        """
        Method to create a buffer pointing to the uncompressed content.
        This method must work lazily, extracting the content only when the buffer is read.
        """

        class ZipContentBuffer(cls.ContentBuffer):
            """
            Class to allow consumption of buffer in a lazy way.
            """

            def mount_compressed_object(self: PackageExtractor.ContentBuffer) -> None:
                """
                Method to initialize the compressed file from the upstream package buffer.
                """
                # Instantiate the buffer of inner content
                self.compressed_object: ZipFile = self.compressor(
                    file=self.source_file_object.content_as_buffer
                )
                
            def mount_buffer(self: PackageExtractor.ContentBuffer) -> None:
                """
                Method to initiate the buffer object if not exists.
                """
                if not self.compressed_object:
                    self.mount_compressed_object()

                self.buffer = self.compressed_object.open(name=self.filename)
                
            def seekable(self) -> bool:
                """
                Method to verify if buffer is seekable.
                This method override the default behavior for better performance to avoid extracting the self.filename.
                """                
                if not self.compressed_object:
                    self.mount_compressed_object()
                
                return self.compressed_object._seekable

        return ZipContentBuffer(
            file_object, cls.compressor_class, internal_file_name, mode, cls
        )

    @classmethod
    def decompress(cls, file_object: BaseFile, overrider: bool, **kwargs: Any) -> bool:
        """
        Method to uncompress the content from a file_object.
        """
        try:
            # We don't need to create the directory because the extractor will create it if not exists.
            extraction_path: str = kwargs.pop("decompress_to")

            # We don't need to reset the buffer before calling it, because it will be reset
            # if already cached. The next time property buffer is called it will reset again.
            with cls.compressor_class(
                file=file_object.content_as_buffer
            ) as compressed_file:  # type: ignore
                # targets as None will extract all data, overwriting existing ones.
                targets: list | None = None

                if not overrider:
                    targets = []
                    for filename in compressed_file.namelist():
                        # Avoid files beginning with `..` or `/` for security reason.
                        if filename[0] == "/" or filename[0:2] == "..":
                            continue

                        if not file_object.storage.exists(
                            file_object.storage.join(extraction_path, filename)
                        ):
                            targets.append(filename)

                    # Avoid calling the extractor if the list is empty.
                    if not targets:
                        return True

                # Concurrent extract file in external file system using a custom pathlib.Path
                # with accessor informed by storage of file_object.
                compressed_file.extractall(
                    path=file_object.storage.get_pathlib_path(extraction_path),
                    members=targets,
                )

        except BadZipFile:
            return False

        return True

    @classmethod
    def extract(cls, file_object: BaseFile, overrider: bool, **kwargs: Any) -> bool:
        """
        Method to extract the information necessary from a file_object.
        """
        if not file_object.save_to:
            return False

        try:
            file_system: Type[StorageEngine] = file_object.storage
            file_class: Type[BaseFile] = file_object.__class__

            # We don't need to reset the buffer before calling it, because it will be reset
            # if already cached. The next time property buffer is called it will reset again.
            with cls.compressor_class(
                file=file_object.content_as_buffer
            ) as compressed_object:  # type: ignore
                for internal_file in compressed_object.infolist():
                    # Skip directories and symbolic link
                    if internal_file.is_dir():
                        continue

                    # Skip inexisting filename if for some reason there is one.
                    if not internal_file.filename:
                        continue

                    # Cast specifically created to fix a mypy error, as internal_file should always have a filename
                    filename: str = str(internal_file.filename)

                    # Skip duplicate only if not choosing to override.
                    if filename in file_object._content_files and not overrider:
                        continue

                    # Create file object for internal file
                    internal_file_object = file_class(
                        path=file_system.join(file_object.save_to, filename),
                        extract_data_pipeline=Pipeline(
                            "filejacket.pipelines.extractor.FilenameAndExtensionFromPathExtractor",
                            "filejacket.pipelines.extractor.MimeTypeFromFilenameExtractor",
                        ),
                        file_system_handler=file_system,
                    )

                    # Update creation and modified date. Zip don't store the created date, only the modified one.
                    # To avoid problem the created date will be consider the same as modified.
                    internal_file_object.create_date = datetime(
                        *internal_file.date_time
                    )
                    internal_file_object.update_date = internal_file_object.create_date

                    # Update size of file
                    internal_file_object.length = internal_file.file_size

                    # Update hash generating the hash file and adding its content
                    hash_file = CRC32Hasher.create_hash_file(
                        object_to_process=internal_file_object,
                        digested_hex_value=str(internal_file.CRC),
                    )
                    internal_file_object.hashes["crc32"] = (
                        str(internal_file.CRC),
                        hash_file,
                        CRC32Hasher,
                    )

                    # Set up action to be extracted instead of to save.
                    internal_file_object._actions.to_extract()

                    # Get mode from type
                    mode: str = "r" if internal_file_object.type == "text" else "rb"

                    # Set up content pointer to internal file using content_buffer
                    internal_file_object.content_as_buffer = cls.content_buffer(
                        file_object=file_object, internal_file_name=filename, mode=mode
                    )

                    # Set up metadata for internal file
                    internal_file_object.meta.hashable = False
                    internal_file_object.meta.internal = True

                    # Add internal file as File object to file.
                    file_object._content_files[filename] = internal_file_object

            # Update metadata and actions.
            file_object.meta.packed = True
            file_object._actions.listed()

        except BadZipFile:
            return False

        return True


class RarCompressedFilesFromPackageExtractor(PackageExtractor):
    """
    Class to extract internal files from rar files.
    """

    extensions: set[str] = {"rar", "cbr"}
    """
    Attribute to store allowed extensions for use in `validator`.
    """
    compressor_class: Type[RarFile] = RarFile
    """
    Attribute to store the current class of compressor for use in `content_buffer` and `decompress` methods.
    """

    @classmethod
    def content_buffer(
        cls, file_object: BaseFile, internal_file_name: str, mode: str = "rb"
    ) -> PackageExtractor.ContentBuffer:
        """
        Method to create a buffer pointing to the uncompressed content.
        This method must work lazily, extracting the content only when the buffer is read.
        """

        class RarContentBuffer(PackageExtractor.ContentBuffer):
            """
            Class to allow consumption of buffer in a lazy way.
            """

            def mount_compressed_object(self: PackageExtractor.ContentBuffer) -> None:
                """
                Method to initialize the compressed file from the upstream package buffer.
                """
                # Instantiate the buffer of inner content
                self.compressed_object: RarFile = self.compressor(
                    file=self.source_file_object.content_as_buffer
                )
                
            def mount_buffer(self: PackageExtractor.ContentBuffer) -> None:
                """
                Method to initiate the buffer object if not exists.
                """
                if not self.compressed_object:
                    self.mount_compressed_object()
                
                self.buffer = self.compressed_object.open(name=self.filename)
                
            def seekable(self) -> bool:
                """
                Method to verify if buffer is seekable.
                This method override the default behavior for better performance to avoid extracting the self.filename.
                """                
                if not self.compressed_object:
                    self.mount_compressed_object()
                
                return self.compressed_object.seekable()
            
        return RarContentBuffer(
            file_object, cls.compressor_class, internal_file_name, mode, cls
        )

    @classmethod
    def decompress(cls, file_object: BaseFile, overrider: bool, **kwargs: Any) -> bool:
        """
        Method to uncompressed the content from a file_object.
        """
        try:
            # We don't need to create the directory because the extractor will create it if not exists.
            extraction_path: str = kwargs.pop("decompress_to")

            # We don't need to reset the buffer before calling it, because it will be reset
            # if already cached. The next time property buffer is called it will reset again.
            with cls.compressor_class(
                file=file_object.content_as_buffer
            ) as compressed_file:
                # targets as None will extract all data, overwriting existing ones.
                targets: list[str] | None = None

                if not overrider:
                    targets = []
                    for filename in compressed_file.namelist():
                        # Avoid files beginning with `..` or `/` for security reason.
                        if filename[0] == "/" or filename[0:2] == "..":
                            continue

                        if not file_object.storage.exists(
                            file_object.storage.join(extraction_path, filename)
                        ):
                            targets.append(filename)

                    # Avoid calling the extractor if the list is empty.
                    if not targets:
                        return True

                # Concurrent extract file in external file system using a custom pathlib.Path
                # with accessor informed by storage of file_object.
                compressed_file.extractall(
                    path=file_object.storage.get_pathlib_path(extraction_path),
                    members=targets,
                )

        except (BadRarFile, NotRarFile):
            return False

        return True

    @classmethod
    def extract(cls, file_object: BaseFile, overrider: bool, **kwargs: Any) -> bool:
        """
        Method to extract the information necessary from a file_object.
        """

        if not file_object.save_to:
            return False

        try:
            file_system: Type[StorageEngine] = file_object.storage
            file_class: Type[BaseFile] = file_object.__class__

            # We don't need to reset the buffer before calling it, because it will be reset
            # if already cached. The next time property buffer is called it will reset again.
            with cls.compressor_class(
                file=file_object.content_as_buffer
            ) as compressed_object:
                for internal_file in compressed_object.infolist():
                    # Skip directories and symbolic link
                    if internal_file.is_dir() or internal_file.is_symlink():
                        continue

                    # Skip inexisting filename if for some reason there is one.
                    if not internal_file.filename:
                        continue

                    # Cast specifically created to fix a mypy error, as internal_file should always have a filename
                    filename: str = str(internal_file.filename)

                    # Skip duplicate only if not choosing to override.
                    if filename in file_object._content_files and not overrider:
                        continue

                    # Create file object for internal file
                    internal_file_object = file_class(
                        path=file_system.join(file_object.save_to, filename),
                        extract_data_pipeline=Pipeline(
                            "filejacket.pipelines.extractor.FilenameAndExtensionFromPathExtractor",
                            "filejacket.pipelines.extractor.MimeTypeFromFilenameExtractor",
                        ),
                        file_system_handler=file_system,
                    )

                    # Update creation and modified date
                    internal_file_object.create_date = internal_file.ctime
                    internal_file_object.update_date = internal_file.mtime

                    # Update size of file
                    internal_file_object.length = internal_file.file_size

                    # Update hash generating the hash file and adding its content
                    if internal_file.CRC:
                        hash_file = CRC32Hasher.create_hash_file(
                            object_to_process=internal_file_object,
                            digested_hex_value=internal_file.CRC,
                        )
                        internal_file_object.hashes["crc32"] = (
                            internal_file.CRC,
                            hash_file,
                            CRC32Hasher,
                        )

                    # Set up action to be extracted instead of to save.
                    internal_file_object._actions.to_extract()

                    # Get mode from type
                    mode: str = "r" if internal_file_object.type == "text" else "rb"

                    # Set up content pointer to internal file using content_buffer
                    internal_file_object.content_as_buffer = cls.content_buffer(
                        file_object=file_object, internal_file_name=filename, mode=mode
                    )

                    # Set up metadata for internal file
                    internal_file_object.meta.hashable = False
                    internal_file_object.meta.internal = True

                    # Add internal file as File object to file.
                    file_object._content_files[filename] = internal_file_object

            # Update metadata and actions.
            file_object.meta.packed = True
            file_object._actions.listed()

        except (BadRarFile, NotRarFile):
            return False

        return True


class SevenZipCompressedFilesFromPackageExtractor(PackageExtractor):
    """
    Class to extract internal files from 7z files.
    """

    extensions: set[str] = {"7z", "cb7"}
    """
    Attribute to store allowed extensions for use in `validator`.
    """
    compressor_class: Type[SevenZipFile] = LazyImportClass(
        "SevenZipFile", from_module="py7zr"
    )
    """
    Attribute to store the current class of compressor for use in `content_buffer` and `decompress` methods.
    """

    @classmethod
    def content_buffer(
        cls, file_object: BaseFile, internal_file_name: str, mode: str = "rb"
    ) -> PackageExtractor.ContentBuffer:
        """
        Method to create a buffer pointing to the uncompressed content.
        This method must work lazily, extracting the content only when the buffer is read.
        """

        class SevenZipContentBuffer(PackageExtractor.ContentBuffer):
            """
            Class to allow consumption of buffer in a lazy way.
            """

            def mount_compressed_object(self: PackageExtractor.ContentBuffer) -> None:
                """
                Method to initialize the compressed file from the upstream package buffer.
                """
                # Instantiate the buffer of inner content
                self.compressed_object: SevenZipFile = self.compressor(
                    file=self.source_file_object.content_as_buffer
                )  # type: ignore
            
            def mount_buffer(self: PackageExtractor.ContentBuffer) -> None:
                """
                Method to initiate the buffer object if not exists.
                """
                if not self.compressed_object:
                    self.mount_compressed_object()

                # Case the packed file don't have content it will return None
                content = self.compressed_object.read(targets=[self.filename])

                if content is None:
                    self.buffer = BytesIO(b"")
                else:
                    self.buffer = next(iter(content.values()))
                    
            def seekable(self) -> bool:
                """
                Method to verify if buffer is seekable.
                This method override the default behavior for better performance to avoid extracting the self.filename.
                """                
                if not self.compressed_object:
                    self.mount_compressed_object()
                    
                return self.compressed_object.fp.seekable()

        return SevenZipContentBuffer(
            file_object, cls.compressor_class, internal_file_name, mode, cls
        )

    @classmethod
    def decompress(cls, file_object: BaseFile, overrider: bool, **kwargs: Any) -> bool:
        """
        Method to uncompressed the content from a file_object.
        """
        from py7zr.exceptions import Bad7zFile

        try:
            # We don't need to create the directory because the extractor will create it if not exists.
            extraction_path: str = kwargs.pop("decompress_to")

            # We don't need to reset the buffer before calling it, because it will be reset
            # if already cached. The next time property buffer is called it will reset again.
            with cls.compressor_class(
                file=file_object.content_as_buffer
            ) as compressed_file:  # type: ignore
                # targets as None will extract all data, overwriting existing ones.
                targets: list[str] | None = None

                if not overrider:
                    targets = []
                    for filename in compressed_file.getnames():
                        # Avoid files beginning with `..` or `/` for security reason.
                        if filename[0] == "/" or filename[0:2] == "..":
                            continue

                        if not file_object.storage.exists(
                            file_object.storage.join(extraction_path, filename)
                        ):
                            targets.append(filename)

                    # Avoid calling the extractor if the list is empty.
                    if not targets:
                        return True

                # Concurrent extract file in external file system using a custom pathlib.Path
                # with accessor informed by storage of file_object.
                compressed_file.extract(
                    path=file_object.storage.get_pathlib_path(extraction_path),
                    targets=targets,
                )

        except Bad7zFile:
            return False

        return True

    @classmethod
    def extract(cls, file_object: BaseFile, overrider: bool, **kwargs: Any) -> bool:
        """
        Method to extract the information necessary from a file_object.
        """
        if not file_object.save_to:
            return False

        from py7zr.exceptions import Bad7zFile

        try:
            cls.validate(file_object)

            file_system: Type[StorageEngine] = file_object.storage
            file_class: Type[BaseFile] = file_object.__class__
            
            # We don't need to reset the buffer before calling it, because it will be reset
            # if already cached. The next time property buffer is called it will reset again.
            with cls.compressor_class(
                file=file_object.content_as_buffer
            ) as compressed_object:  # type: ignore
                compressed_object: FileInfo
                
                for internal_file in compressed_object.list():
                    # Skip directories
                    if internal_file.is_directory:
                        continue

                    # Skip inexistent filename if for some reason there is one.
                    if not internal_file.filename:
                        continue

                    # Cast specifically created to fix a mypy error, as internal_file should always have a filename
                    filename: str = str(internal_file.filename)

                    # Skip duplicate only if not choosing to override.
                    if filename in file_object._content_files and not overrider:
                        continue
                    
                    # Create file object for internal file
                    internal_file_object = file_class(
                        path=file_system.join(file_object.save_to, filename),
                        extract_data_pipeline=Pipeline(
                            "filejacket.pipelines.extractor.FilenameAndExtensionFromPathExtractor",
                            "filejacket.pipelines.extractor.MimeTypeFromFilenameExtractor",
                        ),
                        file_system_handler=file_system,
                    )

                    # Update creation and modified date
                    internal_file_object.create_date = internal_file.creationtime
                    internal_file_object.update_date = internal_file.creationtime

                    # Update size of file
                    internal_file_object.length = internal_file.uncompressed

                    # Update hash generating the hash file and adding its content
                    hash_file = CRC32Hasher.create_hash_file(
                        object_to_process=internal_file_object,
                        digested_hex_value=internal_file.crc32,
                    )
                    internal_file_object.hashes["crc32"] = (
                        internal_file.crc32,
                        hash_file,
                        CRC32Hasher,
                    )

                    # Set up action to be extracted instead of to save.
                    internal_file_object._actions.to_extract()

                    # Get mode from type
                    mode = "r" if internal_file_object.type == "text" else "rb"

                    # Set up content pointer to internal file using content_buffer
                    internal_file_object.content_as_buffer = cls.content_buffer(
                        file_object=file_object, internal_file_name=filename, mode=mode
                    )

                    # Set up metadata for internal file
                    internal_file_object.meta.hashable = False
                    internal_file_object.meta.internal = True

                    # Add internal file as File object to file.
                    file_object._content_files[filename] = internal_file_object

            # Update metadata and actions.
            file_object.meta.packed = True
            file_object._actions.listed()

        except Bad7zFile:
            return False

        return True
