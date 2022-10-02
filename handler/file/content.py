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
`handler <at> gabrielfontenelle.com` can be used.
"""

from io import StringIO, IOBase, BytesIO

from ..pipelines.renamer import UniqueRenamer
from ..pipelines import Pipeline
from ..exception import SerializerError
from .descriptor import InternalFilesDescriptor

__all__ = [
    "FileContent",
    "FilePacket",
]


class FileContent:
    """
    Class that store file instance content.
    """
    # Properties
    is_binary = False
    """
    Type of stream used in buffer for content.
    """

    # Buffer handles
    buffer = None
    """
    Stream for file`s content.
    """
    related_file_object = None
    """
    Variable to work as shortcut for the current related object for the hashes and other data.
    """
    _block_size = 256
    """
    Block size of file to be loaded in each step of iterator.
    """
    _buffer_encoding = 'utf-8'
    """
    Encoding default used to convert the buffer to string.
    """
    _iterable_in_use = False
    """
    Indicate whether the method next is currently being used to consume the buffer.
    """

    # Cache handles
    cache_content = False
    """
    Whether the content should be cached.
    """
    cache_in_memory = True
    """
    Whether the cache will be made in memory.
    """
    cache_in_file = False
    """
    Whether the cache will be made in filesystem.
    """
    cached = False
    """
    Whether the content as whole was cached. Being True the current buffer will point to a stream
    of `_cached_content`.
    """
    _cached_content = None
    """
    Stream for file`s content cached.
    """
    _cached_path = None
    """
    Complete path for temporary file used as cache.
    """

    def __init__(self, raw_value, force=False, **kwargs):
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
                raise SerializerError(f"Class {self.__class__.__name__} doesn't have an attribute called {key}.")

        if "buffer" in kwargs:
            # We already set up buffer, so we don't need to set up it from raw_value
            return

        if not raw_value:
            raise ValueError(f"Value pass to FileContent must not be empty!")

        # Binary value of related_file_object should be be set up here, as it came from attribute is_binary from
        # content.
        if isinstance(raw_value, str):
            raw_value = StringIO(raw_value)
        elif isinstance(raw_value, bytes):
            raw_value = BytesIO(raw_value)
        elif isinstance(raw_value, IOBase):
            if not hasattr(raw_value, "mode") and not isinstance(raw_value, (StringIO, BytesIO)):
                raise ValueError(f"The value specified for content of type {type(raw_value)} don't have the attribute"
                                 f"mode that allow for identification of type of content: binary or text.")
        else:
            raise ValueError(f"parameter `value` informed in FileContent is not a valid type"
                             f" {type(raw_value)}! We were expecting str, bytes or IOBase.")

        # Set attribute is_binary based on instance type.
        self.is_binary = isinstance(raw_value, BytesIO) or 'b' in getattr(raw_value, 'mode', '')

        # Add content (or content converted to Stream) as buffer
        self.buffer = raw_value

        # Set content to be cached.
        if not self.buffer.seekable() or force:
            self.cache_content = True
            self.cached = False

        # Default buffer for cache
        self._cached_content = None

    def __iter__(self):
        """
        Method to return current object as iterator. As it already implements __next__ we just return the current
        object.
        """
        return self

    def __next__(self):
        """
        Method that defines the behavior of iterable blocks of current object.
        This method has the potential to double the memory size of current object storing
        the whole buffer in memory.

        This method will cache content in file or in memory depending on value of `cache_content`, `cache_in_memory` and
        `cache_in_file`. For caching in file, it will generate a unique filename in a temporary directory.
        """
        # Flag to avoid calling this method with self.read()
        self._iterable_in_use = True

        block = self.buffer.read(self._block_size)

        # This end the loop if block is None, b'' or ''.
        if not block and block != 0:
            # Change buffer to be cached content
            if self.cache_content and not self.cached:
                if self.cache_in_memory:
                    class_name = BytesIO if self.is_binary else StringIO
                    self.buffer = class_name(self._cached_content)
                    self.cached = True
                elif self.cache_in_file:
                    # Buffer receive stream from file
                    mode = 'r' if self.is_binary else 'rb'
                    self.buffer = self.related_file_object.storage.open_file(self._cached_path, mode=mode)
                    self.cached = True

            # Reset buffer to begin from first position
            self.reset()

            self._iterable_in_use = False

            raise StopIteration()

        # Cache content
        if self.cache_content and not self.cached:
            # Cache content in memory only
            if self.cache_in_memory:
                if self._cached_content is None:
                    self._cached_content = block
                else:
                    self._cached_content += block
            # Cache content in temporary file
            elif self.cache_in_file:
                if not self._cached_path:
                    # Create new temporary file using renamer pipeline to obtain
                    # a unique filename for temporary file.
                    temp = self.related_file_object.storage.get_temp_directory()
                    filename, extension = UniqueRenamer.get_name(
                        directory_path=temp,
                        filename=self.related_file_object.filename,
                        extension=self.related_file_object.extension
                    )
                    formatted_extension = f'.{extension}' if extension else ''
                    if temp[-1] != self.related_file_object.storage.sep:
                        temp += self.related_file_object.storage.sep

                    self._cached_path = temp + filename + formatted_extension

                # Open file, append block to file and close file.
                write_mode = 'b' if self.is_binary else ''
                self.related_file_object.storage.save_file(self._cached_path, block, file_mode='a',
                                                           write_mode=write_mode)

        return block

    @property
    def __serialize__(self):
        """
        Method to allow dir and vars to work with the class simplifying the serialization of object.
        """
        attributes = {
            "is_binary",
            "buffer",
            "related_file_object",
            "_block_size",
            "_buffer_encoding",
            "cache_content",
            "cache_in_memory",
            "cache_in_file",
            "cached",
            "_cached_content",
            "_cached_path",
        }

        return {key: getattr(self, key) for key in attributes}

    @property
    def should_load_to_memory(self):
        """
        Method to indicate whether the current buffer is seekable or not. Not seekable object should
        """
        return not self.buffer.seekable() and not self.cached

    @property
    def content(self):
        """
        Method to load in memory the content of the file.
        This method uses the buffer cached, if the file wasn't cached before this method will cache it, and load
        the data in memory from the cache returning the content.
        """
        old_cache_in_memory = self.cache_in_memory
        old_cache_in_file = self.cache_in_file

        # Set cache to load in memory
        if not (self.cache_in_memory or self.cache_in_file):
            self.cache_in_memory = True
            self.cache_in_file = False

        if self._cached_content is None or self._cached_path is None:
            # Consume content if not loaded and cache it
            while True:
                try:
                    next(self)
                except StopIteration:
                    break

        # Content in case that it was loaded in memory. If not, it will be None and override below.
        content = self._cached_content

        # Override `content` with content from file.
        if self.cache_in_file and self._cached_path:
            mode = 'rb' if self.is_binary else 'r'
            buffer = self.related_file_object.storage.open_file(self._cached_path, mode=mode)
            content = buffer.read()
            self.related_file_object.storage.close_file(buffer)

        self.cache_in_memory = old_cache_in_memory
        self.cache_in_file = old_cache_in_file

        return content

    @property
    def content_as_buffer(self):
        """
        Method to obtain the content as a buffer, loading it in memory if it is allowed and is not loaded already.
        """
        if self.should_load_to_memory:
            # We should load the current buffer to memory before using it.
            # Load content to memory with `self.content` and return the adequate buffer.
            buffer_class = BytesIO if self.is_binary else StringIO
            return buffer_class(self.content)
        else:
            # Should not reach here if object is not seekable, but
            # to avoid problems with override of `should_load_to_memory` property
            # we check before using seek to reset the content.
            self.reset()

            return self.buffer

    def reset(self):
        """
        Method to reset the content cached or buffer if allowed.
        """
        if self.buffer.seekable():
            self.buffer.seek(0)

    def read(self, size=None):
        """
        Method to return part or whole content cached or buffered.
        This method should not be used while the iter(self) is being consumed in a loop, due to concurrency problem
        that may arise calling multiple times buffer.read(), which can lead to data loss.
        """

        if self._iterable_in_use:
            raise RecursionError(f"Method read cannot be used while the iterable of {self} is being consumed.")

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
    """

    _internal_files = InternalFilesDescriptor()
    """
    Dictionary used for storing the internal files data. Each file is reserved through its <directory>/<name> inside
    the package.
    """

    history = None
    """
    Storage internal files to allow browsing old ones for current BaseFile.
    """

    # Pipelines
    extract_data_pipeline = Pipeline(
        'handler.pipelines.extractor.SevenZipCompressedFilesFromPackageExtractor',
        'handler.pipelines.extractor.RarCompressedFilesFromPackageExtractor',
        'handler.pipelines.extractor.TarCompressedFilesFromPackageExtractor',
        'handler.pipelines.extractor.ZipCompressedFilesFromPackageExtractor',
    )
    """
    Pipeline to extract data from multiple sources. For it to work, its classes should implement stopper as True.
    """

    def __init__(self, **kwargs):
        """
        Method to create the current object using the keyword arguments.
        """
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
            else:
                raise SerializerError(f"Class {self.__class__.__name__} doesn't have an attribute called {key}.")

    def __getitem__(self, item):
        """
        Method to serve as shortcut to allow return of item in _internal_files in instance of FilePacket.
        This method will try to retrieve an element from the dictionary by index if item is numeric.
        """
        if isinstance(item, int):
            return list(self.files())[item]

        return self._internal_files[item]

    def __contains__(self, item):
        """
        Method to serve as shortcut to allow verification if item contains in _internal_files in instance of FilePacket.
        """
        return item in self._internal_files

    def __setitem__(self, key, value):
        """
        Method to serve as shortcut to allow adding an item in _internal_files in instance of FilePacket.
        """
        # Restrict type of key being insert to allow __getitem__ to return from list when using
        # a numeric value.
        if isinstance(key, int):
            raise ValueError("Parameter key to __setitem__ in class FilePacket cannot be numeric.")

        self._internal_files[key] = value

    def __len__(self):
        """
        Method that defines the size of current object. We will consider the size as being the same of
        `_internal_files`
        """
        return len(self._internal_files)

    def __iter__(self):
        """
        Method to return current object as iterator. As it already implements __next__ we just return the current
        object.
        """
        return iter(self._internal_files.items())

    @property
    def __serialize__(self):
        """
        Method to allow dir and vars to work with the class simplifying the serialization of object.
        """
        attributes = {"_internal_files", "extract_data_pipeline", "history"}

        return {key: getattr(self, key) for key in attributes}

    def clean_history(self):
        """
        Method to clean the history of internal_files.
        The data will still be in memory while the Garbage Collector don't remove it.
        """
        self.history = []

    def files(self):
        """
        Method to obtain the list of objects File stored at `_internal_files`.
        """
        return self._internal_files.values()

    def names(self):
        """
        Method to obtain the list of names of internal files stored at `_internal_files`.
        """
        return self._internal_files.keys()

    def reset(self):
        """
        Method to clean the internal files keeping a historic of changes.
        """
        if self.history is None:
            self.history = []

        # Add current internal files to memory
        self.history.append(self._internal_files)

        # Reset the internal files
        self._internal_files = {}
