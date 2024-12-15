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

from base64 import b64encode
from io import StringIO, BytesIO
from typing import Iterator, Any, TYPE_CHECKING, IO

from ..adapters.storage import LinuxFileSystem
from ..exception import (
    CacheContentNotSeekableError,
    OperationNotAllowed,
    SerializerError,
    EmptyContentError,
    ImproperlyConfiguredFile,
)
from ..pipelines import Pipeline
from ..pipelines.extractor.package import PackageExtractor

if TYPE_CHECKING:
    from . import BaseFile
    from ..engines.storage import StorageEngine


__all__ = ["FileContent", "FilePacket", "CacheInFile", "CacheInMemory", "NonCache"]


class BufferStr:
    """
    Class to abstract conversion from a type of buffer to another in the FileContent.
    This class is used for handling buffer for strings.
    """

    read_mode: str = "r"
    write_mode: str = ""
    buffer_class: type = StringIO
    binary: bool = False
    encoding: str = "utf-8"
    newline: str | None = ""

    @classmethod
    def to_bytes(cls, value: str) -> bytes:
        """
        Method to convert the value to bytes.
        """
        return value.encode(cls.encoding)

    @classmethod
    def to_base64(cls, value: str) -> bytes:
        """
        Method to convert the value to representation of Base64 in string ASCII.
        """
        return b64encode(cls.to_bytes(value)).decode("ascii")

    @classmethod
    def to_buffer(cls, value: str) -> StringIO:
        """
        Method to initialize the buffer to handle string.
        """
        return cls.buffer_class(value)


class BufferBytes:
    """
    Class to abstract conversion from a type of buffer to another in the FileContent.
    This class is used for handling buffer for bytes.
    """

    read_mode: str = "rb"
    write_mode: str = "b"
    buffer_class: type = BytesIO
    binary: bool = True
    encoding: str = "utf-8"
    newline: str | None = None

    @classmethod
    def to_bytes(cls, value: bytes) -> bytes:
        """
        Method to convert the value to bytes.
        """
        return value

    @classmethod
    def to_base64(cls, value: bytes) -> bytes:
        """
        Method to convert the value to representation of Base64 in string ASCII.
        """
        return b64encode(cls.to_bytes(value)).decode("ascii")

    @classmethod
    def to_buffer(cls, value: bytes) -> BytesIO:
        """
        Method to initialize the buffer to handle bytes.
        """
        return cls.buffer_class(value)


class CacheInFile:
    """
    Class to abstract use of cache in FileContent.
    This class abstract the caching of content in a temporary file (the file is not deleted though).
    """

    cached = False
    """
    Indicate whether the cache of content was completed. 
    """
    storage: type[StorageEngine] = LinuxFileSystem
    """
    Storage for local filesystem to create the temporary file for caching. 
    """
    cached_file: str
    """
    Complete path for temporary file used as cache.
    """

    def __init__(self: CacheInFile, buffer_helper: BufferStr | BufferBytes) -> None:
        """ """
        self.cached_file = self.storage.get_unique_temp_file()
        self.buffer_helper = buffer_helper

    @property
    def content(self):
        """ """
        return self.load_from_cache()

    @content.setter
    def content(self, value):
        """ """
        self.save_and_return(value)

    def save_and_return(self: CacheInFile, content: str | bytes):
        """ """
        # Open file, append block to file and close file.
        self.storage.write_to_file(
            self.cached_file,
            content,
            file_mode="a",
            write_mode=self.buffer_helper.write_mode,
        )

        return content

    def load_from_cache(self: CacheInFile) -> str | bytes:
        """ """
        buffer = self.storage.open_file(
            self.cached_file, mode=self.buffer_helper.read_mode
        )
        content = buffer.read()
        self.storage.close_file(buffer)

        if not content:
            raise EmptyContentError("No content stored in `{self.cached_file}`.")

        return content

    def load_buffer_from_cache(self: CacheInFile) -> BytesIO | StringIO:
        """ """
        # Buffer receive stream from file
        return self.storage.open_file(
            self.cached_file, mode=self.buffer_helper.read_mode
        )

    def consume(self: CacheInFile, iterator: Iterator) -> None:
        """ """

        # Consume content if not loaded and cache it
        if not self.cached:
            while True:
                try:
                    next(iterator)
                except StopIteration:
                    break

    def set_cached(self: CacheInFile):
        """ """
        self.cached = True


class CacheInMemory:
    """
    Class to abstract use of cache in FileContent.
    This class abstract the caching of content in memory.
    """

    cached = False
    """
    Indicate whether the cache of content was completed. 
    """
    content: BytesIO | StringIO
    content = None
    """
    """

    def __init__(self: CacheInMemory, buffer_helper: BufferStr | BufferBytes) -> None:
        """ """
        self.content = buffer_helper(newline=buffer_helper.newline)

    def save_and_return(self: CacheInMemory, content: bytes | str):
        """ """
        self.content.write(content)
        return content

    def load_from_cache(self: CacheInMemory) -> str | bytes:
        """ 
        """
        self.content.seek(0)
        return self.content.read()

    def load_buffer_from_cache(self: CacheInMemory) -> BytesIO | StringIO:
        """ """
        return self.content

    def consume(self: CacheInMemory, iterator: Iterator) -> None:
        """ """

        # Consume content if not loaded and cache it
        if not self.cached:
            while True:
                try:
                    next(iterator)
                except StopIteration:
                    break

    def set_cached(self: CacheInMemory):
        """ """
        self.cached = True


class NonCache:
    """
    Class to abstract use of cache in FileContent.
    This class abstract the absence of caching. For the overall abstractions of loading and caching file to work in
    FileContent this class was created allow use of no cache at all.
    """

    cached = False
    """
    Indicate whether the cache of content was completed. 
    """
    content = None
    """
    """

    def __init__(self: CacheInMemory, buffer_helper: BufferStr | BufferBytes) -> None:
        """ """
        ...

    def save_and_return(self: NonCache, content: str | bytes):
        """ """
        return content

    def load_from_cache(self: NonCache) -> str | bytes:
        """ """
        raise OperationNotAllowed(
            "Class for cache, `NonCache`, does not store content and thus not allow `load_from_cache`."
        )

    def load_buffer_from_cache(self: NonCache):
        """ """
        raise OperationNotAllowed(
            "Class for cache, `NonCache`, does not store content and thus not allow `load_buffer_from_cache`."
        )

    def consume(self: NonCache, iterator: Iterator) -> None:
        """ """
        raise OperationNotAllowed(
            "Class for cache, `NonCache`, does not store content and thus not allow `consume`."
        )

    def set_cached(self: NonCache):
        """ """
        ...


class FileContent:
    """
    Class that store file instance content.
    """

    related_file_object: BaseFile
    related_file_object = None
    """
    Variable to work as shortcut for the current related object for the hashes and other data.
    """
    _block_size: int = 256
    """
    Block size of file to be loaded in each step of iterator.
    """
    _buffer_encoding: str = "utf-8"
    """
    Encoding default used to convert the buffer to string.
    """
    _iterable_in_use: bool = False
    """
    Indicate whether the method next is currently being used to consume the buffer.
    """

    # Buffer handles
    buffer: BytesIO | StringIO | IO
    buffer = None
    """
    Stream for file`s content.
    """
    buffer_helper: BufferStr | BufferBytes
    buffer_helper = None
    """
    Helper to facilitate conversion of stream for saving and loading the file`s content.
    """

    # Cache handles
    cache_helper: type[CacheInFile] | type[CacheInMemory] | type[NonCache]
    cache_helper = None
    """
    Helper to facilitate caching of content. It defines which type of caching is performed with file`s content. 
    This helper can be replaced with a class that saves data in a external repository like redis. To use any class the few requirements 
    are to implement the method `save_and_return` and `load_from_cache`.
    """
    _cached_content: CacheInFile | CacheInMemory | NonCache
    _cached_content = None
    """
    File`s content cached stored through the cache abstraction instantiated from cache_helper.
    """

    @classmethod
    def from_str(cls, value: str, force_cache) -> FileContent:
        obj = cls.__new__(cls)  # Does not call __init__
        super(
            FileContent, obj
        ).__init__()  # Don't forget to call any polymorphic base class initializers

        obj.buffer_class = BufferStr
        obj.buffer = BufferStr.to_buffer(value)

        ...

        return obj

    def __init__(
        self,
        raw_value: str
        | bytes
        | BytesIO
        | StringIO
        | PackageExtractor.ContentBuffer
        | None = None,
        force: bool = False,
        **kwargs: Any,
    ) -> None:
        """
        Initial method that set up the buffer to be used.
        The parameter `force` when True will force usage of cache even if is IO is seekable.
        """
        # Process kwargs before anything, because buffer can be already set up in kwargs, as this
        # init can be used for serialization and deserialization.
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
            else:
                raise SerializerError(
                    f"Class {self.__class__.__name__} doesn't have an attribute called {key}."
                )

        if "buffer" in kwargs:
            # We already set up buffer, so we don't need to set up it from raw_value
            return

        if not raw_value:
            raise ValueError("Value pass to FileContent must not be empty!")

        # Binary value of related_file_object should be be set up here, as it came from attribute is_binary from
        # content.
        if isinstance(raw_value, str):
            # Convert raw content to buffer
            self.buffer_helper = BufferStr()
            raw_value = self.buffer_helper.to_buffer(raw_value)
        elif isinstance(raw_value, bytes):
            # Convert raw content to buffer
            self.buffer_helper = BufferBytes()
            raw_value = self.buffer_helper.to_buffer(raw_value)
        elif isinstance(raw_value, StringIO):
            # Content is buffered, so don't need to convert it.
            self.buffer_helper = BufferStr()
        elif isinstance(raw_value, BytesIO):
            # Content is buffered, so don't need to convert it.
            self.buffer_helper = BufferBytes()
        elif not (hasattr(raw_value, "seekable") or hasattr(raw_value, "read")):
            raise ValueError(
                f"The parameter `raw_value` informed in FileContent is not a valid type {type(raw_value)}! "
                "We were expecting str, bytes or a class that implements `seekable`, `read` and `mode` like `IOBase`."
            )
        elif not hasattr(raw_value, "mode"):
            raise ValueError(
                f"The value specified for content of type {type(raw_value)} don't have the attribute"
                "mode that allow for identification of type of content: binary or text."
            )
        else:
            self.buffer_helper = (
                BufferBytes() if "b" in getattr(raw_value, "mode", "") else BufferStr()
            )

        # Add content (or content converted to Stream) as buffer
        self.buffer = raw_value

        # Get encoding from raw value so that conversion to bytes has the same result from external hash file.
        if hasattr(raw_value, "encoding"):
            self.buffer_helper.encoding = raw_value.encoding

        if self.cache_helper is None:
            self.cache_helper = NonCache

        # Set content to be cached.
        if not self.buffer.seekable() or force:
            self.cache_helper = CacheInMemory

    def __iter__(self) -> Iterator[bytes | str | None]:
        """
        Method to return current object as iterator. As it already implements __next__ we just return the current
        object.
        """
        if self._cached_content is None:
            self._cached_content = self.cache_helper(buffer_helper=self.buffer_helper)
        
        return self

    def __next__(self) -> bytes | str:
        """
        Method that defines the behavior of iterable blocks of current object.
        This method has the potential to double the memory size of current object storing
        the whole buffer in memory.

        This method will cache content in file, or in memory depending on the class of the `cache_helper`.
        """
        # Flag to avoid calling this method with self.read()
        self._iterable_in_use = True

        block: str | bytes | None = self.buffer.read(self._block_size)

        if not block and block != 0:
            if not self.cached:
                # Change buffer to be cached content
                try:
                    self.buffer = self._cached_content.load_buffer_from_cache()
                    self._cached_content.set_cached()

                except OperationNotAllowed:
                    # Do nothing case operation is not allowed.
                    ...

            # Reset buffer to begin from first position
            self.reset()

            self._iterable_in_use = False

            raise StopIteration()

        if not self.cached:
            block = self._cached_content.save_and_return(block)

        return block

    @property
    def __serialize__(self) -> dict[str, Any]:
        """
        Method to allow dir and vars to work with the class simplifying the serialization of object.
        """
        attributes = {
            "buffer",
            "buffer_helper",
            "cache_helper",
            "related_file_object",
            "_block_size",
            "_buffer_encoding",
            "cached",
            "_cached_content",
        }

        return {key: getattr(self, key) for key in attributes}

    @property
    def should_load_to_memory(self) -> bool:
        """
        Method to indicate whether the current buffer is seekable or not. Not seekable object should be loaded to cache.
        """
        seekable = self.buffer.seekable()

        if not seekable and self.cached:
            raise CacheContentNotSeekableError(
                f"The cache helper `{self.cache_helper.__name__}` does not produced a seekable buffer"
            )

        return not seekable and not self.cached

    @property
    def cached(self):
        """
        Method to verify if content was cached based on the attribute `cached` in `_cached_content`.
        """
        return self._cached_content and self._cached_content.cached

    @property
    def content(self) -> bytes | str | None:
        """
        Method to load in memory the content of the file.
        This method uses the buffer cached, if the file wasn't cached before this method will cache it, and load
        the data in memory from the cache returning the content.

        This method will not cache the content in memory if `self.cache_helper` is `NonCache`.
        """
        if self._cached_content is None:
            self._cached_content = self.cache_helper(buffer_helper=self.buffer_helper)

        try:
            # Consume content passing the iterator to the cache class.
            # The `NonCache` class will not, and should not, perform any action on the iterator.
            self._cached_content.consume(iterator=self)

            return self._cached_content.load_from_cache()

        except OperationNotAllowed as e:
            raise ImproperlyConfiguredFile(
                f"The file {self.related_file_object} is not set-up to load to memory its content. "
                "You should call `_content.content_as_buffer` instead of `_content.content`"
            ) from e
        except EmptyContentError as e:
            raise EmptyContentError(
                f"No content was loaded for file {self.related_file_object.complete_filename}"
            ) from e

    @property
    def content_as_buffer(self) -> BytesIO | StringIO:
        """
        Method to obtain the content as a buffer, loading it in memory if it is allowed and is not loaded already.
        """
        if self.should_load_to_memory:
            # We should load the current buffer to memory before using it.
            # Load content to memory with `self.content` and return the adequate buffer.
            try:
                return self.buffer_helper.to_buffer(self.content)
            except ImproperlyConfiguredFile:
                # Change cache to load from memory because the current `cache_helper` does not consume the content
                # and save it in a cache.
                self._cached_content = CacheInMemory()
                self._cached_content.consume(iterator=self)

                return self._cached_content.load_buffer_from_cache()

        else:
            # Should not reach here if object is not seekable, but
            # to avoid problems with override of `should_load_to_memory` property
            # we check before using seek to reset the content.
            self.reset()

            return self.buffer

    @property
    def content_as_bytes(self) -> bytes | None:
        """
        Method to obtain the content as bytes.
        This method should not be used to convert a content buffered and not cached to byte.
        """
        return self.buffer_helper.to_bytes(self.content)

    @property
    def content_as_base64(self) -> bytes | None:
        """
        Method to obtain the content as a base64 encoded, loading it in memory if it is allowed and is not
        loaded already.
        TODO: Change the code to work with BaseIO to avoid loading all content to memory for larger files.
        """
        try:
            # Load content and convert to base64
            return self.buffer_helper.to_base64(self.content)
        except (EmptyContentError, ImproperlyConfiguredFile):
            ...

        try:
            # No content found, try again with buffer loading the whole buffer in memory.
            return self.buffer_helper.to_base64(self.content_as_buffer.read())
        except OperationNotAllowed:
            ...

        return None

    @property
    def is_binary(self):
        """
        Type of stream used in buffer for content.
        """
        return self.buffer_helper.binary

    @property
    def is_seekable(self):
        """
        If content cached or buffered support seek.
        """
        return self.buffer.seekable()

    def reset(self) -> None:
        """
        Method to reset the content cached or buffer if allowed.
        """
        if self.is_seekable:
            self.buffer.seek(0)

    def read(self, size: int | None = None) -> bytes | str | None:
        """
        Method to return part or whole content cached or buffered.
        This method should not be used while the iter(self) is being consumed in a loop, due to concurrency problem
        that may arise calling multiple times buffer.read(), which can lead to data loss.
        """

        if self._iterable_in_use:
            raise RecursionError(
                f"Method read cannot be used while the iterable of {self} is being consumed."
            )

        if not size:
            # Read the whole content
            return self.content

        # Save original buffer size to allow restoring it after calling __next__()
        original_block_size = self._block_size
        self._block_size = size

        content = self.__next__()
        # Reset the size of buffer to original one
        self._block_size = original_block_size

        # Disable flag _iterable_in_use active because of calling __next__()
        self._iterable_in_use = False

        return content


class FilePacket:
    """
    Class that store internal files from file instance content.
    TODO: Reduce memory usage for listing File from buffer.
    """
    
    _internal_files: dict[str, tuple[BaseFile, int]]
    """
    Dictionary used for storing the internal files data. Each file is reserved through its <directory>/<name> inside
    the package.
    This must be instantiated at `__init__` method.
    """
    
    history: list
    history = None
    """
    Storage internal files to allow browsing old ones for current BaseFile.
    """
    length: int = 0
    """
    Size of file content unpacked.
    """

    # Pipelines
    unpack_data_pipeline: Pipeline = Pipeline(
        "filejacket.pipelines.extractor.SevenZipCompressedFilesFromPackageExtractor",
        "filejacket.pipelines.extractor.RarCompressedFilesFromPackageExtractor",
        "filejacket.pipelines.extractor.TarCompressedFilesFromPackageExtractor",
        "filejacket.pipelines.extractor.ZipCompressedFilesFromPackageExtractor",
    )
    """
    Pipeline to extract data from multiple sources. For it to work, its classes should implement stopper as True.
    """

    def __init__(self: FilePacket, **kwargs: Any) -> None:
        """
        Method to create the current object using the keyword arguments.
        """
        # Set class dict attribute
        self._internal_files = {}
        self.length = 0

        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
            else:
                raise SerializerError(
                    f"Class {self.__class__.__name__} doesn't have an attribute called {key}."
                )

    def __getitem__(self: FilePacket, item: int | str) -> tuple[BaseFile, int]:
        """
        Method to serve as shortcut to allow return of item in _internal_files in instance of FilePacket.
        This method will try to retrieve an element from the dictionary by index if item is numeric.
        """
        if isinstance(item, int):
            return list(self.files())[item]

        return self._internal_files[item]

    def __contains__(self: FilePacket, item: str) -> bool:
        """
        Method to serve as shortcut to allow verification if item contains in _internal_files in instance of FilePacket.
        """
        return item in self._internal_files

    def __setitem__(self: FilePacket, key: str, value: BaseFile) -> None:
        """
        Method to serve as shortcut to allow adding an item in _internal_files in instance of FilePacket.
        """
        # Restrict type of key being insert to allow __getitem__ to return from list when using
        # a numeric value.
        if isinstance(key, int):
            raise ValueError(
                "Parameter key to __setitem__ in class FilePacket cannot be numeric."
            )
        length = len(value)
        self.length += length
        self._internal_files[key] = value, length

    def __len__(self: FilePacket) -> int:
        """
        Method that defines the size of current object. We will consider the size as being the same of
        `_internal_files`
        """
        return len(self._internal_files)

    def __iter__(self: FilePacket) -> Iterator[tuple[BaseFile, int]]:
        """
        Method to return current object as iterator. As it already implements __next__ we just return the current
        object.
        """
        return iter(self._internal_files.items())

    @property
    def __serialize__(self: FilePacket) -> dict[str, Any]:
        """
        Method to allow dir and vars to work with the class simplifying the serialization of object.
        """
        attributes = {"_internal_files", "unpack_data_pipeline", "history", "length"}

        return {key: getattr(self, key) for key in attributes}

    def clean_history(self: FilePacket) -> None:
        """
        Method to clean the history of internal_files.
        The data will still be in memory while the Garbage Collector don't remove it.
        """
        self.history = []

    def files(self: FilePacket) -> list[BaseFile]:
        """
        Method to obtain the list of objects File stored at `_internal_files`.
        """
        return [i[0] for i in self._internal_files.values()]
    
    def files_length(self: FilePacket) -> list[int]:
        """
        Method to obtain the list of length of File stored at `_internal_files`.
        """
        return [i[1] for i in self._internal_files.values()]
    
    def names(self: FilePacket) -> list[str]:
        """
        Method to obtain the list of names of internal files stored at `_internal_files`.
        """
        return list(self._internal_files.keys())

    def reset(self: FilePacket) -> None:
        """
        Method to clean the internal files keeping a history of changes.
        """
        if self.history is None:
            self.clean_history()

        if self._internal_files:
            # Add current internal files to memory
            self.history.append(self._internal_files)

            # Reset the internal files
            self._internal_files = {}
