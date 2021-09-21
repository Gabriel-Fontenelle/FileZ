# first-party
from io import IOBase, StringIO, BytesIO
from os import name

from handler.mimetype import LibraryMimeTyper
from handler.pipelines.comparer import (
    BinaryCompare,
    DataCompare,
    HashCompare,
    SizeCompare,
    TypeCompare
)
# modules
from handler.pipelines.extracter import (
    ContentFromSourceExtracter,
    FileSystemDataExtracter,
    FilenameAndExtensionFromPathExtracter,
    FilenameFromMetadataExtracter,
    FilenameFromURLExtracter,
    HashFileExtracter,
    MetadataExtracter,
    MimeTypeFromContentExtracter,
    MimeTypeFromFilenameExtracter,
)
from handler.pipelines.hasher import (
    MD5Hasher,
    SHA256Hasher
)
from .exception import (
    ImproperlyConfiguredFile,
    NoInternalContentError,
    OperationNotAllowed,
    ReservedFilenameError,
    ValidationError
)
from .handler import LinuxFileSystem, WindowsFileSystem, URI
from .pipelines import Pipeline
from .pipelines.renamer import WindowsRenamer


__all__ = [
    'ContentFile',
    'DownloadFile',
    'File',
    'StreamFile'
]


class CacheDescriptor:
    """
    Descriptor class to storage data for instance`s cache.
    This class is used for FileHashes._cache.
    """

    def __get__(self, instance, cls=None):
        """
        Method `get` to automatically set-up empty values in a instance.
        """
        if instance is None:
            return self

        res = instance.__dict__['_cache'] = {}
        return res


class FileState:
    """
    Class that store file instance state.
    """

    adding = True
    """
    Indicate whether an object was already saved or not. If true, we will consider this a new, unsaved
    object in the current file`s filesystem.
    """
    renaming = False
    """
    Indicate whether an object is schedule to being renamed in the current file`s filesystem.
    """
    changing = False
    """
    Indicate whether an object has changed or not. If true, we will consider that the current content was
    changed but not saved yet.  
    """


class FileMetadata:
    """
    Class that store file instance metadata.
    """

    packed = False
    """
    Indicate whether an object was packed in a container or not. As example: .rar, .epub, .tar. 
    """
    compressed = False
    """
    Indicate whether an object was compressed or not. Different from packed, an object can the packed and not 
    compressed or it could be both packed and compressed.
    """
    lossless = False
    """
    Indicate whether an object was lossless compressed or not. 
    """
    hashable = True
    """
    Indicate whether an object can have its hash saved or not. Internal packed files cannot have hash saved to file, 
    it can be generate just not saved in the package.
    """


class FileActions:
    """
    Class that store file instance actions to be performed.
    """

    save = False
    """
    Indicate whether an object should be saved or not.
    """
    extract = False
    """
    Indicate whether an object should be extracted or not.
    File inside another file should be extract and not saved.
    """
    rename = False
    """
    Indicate whether an object should be renamed or not.
    """
    hash = False
    """
    Indicate whether an object should be hashed or not.
    """
    was_saved = False
    """
    Indicate whether an object was successfully saved.
    """
    was_extracted = False
    """
    Indicate whether an object was successfully extracted.
    """
    was_renamed = False
    """
    Indicate whether an object was successfully renamed.
    """
    was_hashed = False
    """
    Indicate whether an object was successfully hashed.
    """

    def to_extract(self):
        """
        Method to set-up the action of save file.
        """
        self.extract = True
        self.was_extracted = False

    def extracted(self):
        """
        Method to change the status of `to extract` to `extracted` file.
        """
        self.extract = False
        self.was_extracted = True

    def to_save(self):
        """
        Method to set-up the action of save file.
        """
        self.save = True
        self.was_saved = False

    def saved(self):
        """
        Method to change the status of `to save` to `saved` file.
        """
        self.save = False
        self.was_saved = True

    def to_rename(self):
        """
        Method to set-up the action of rename file.
        """
        self.rename = True
        self.was_renamed = False
        pass

    def renamed(self):
        """
        Method to change the status of `to rename` to `renamed` file.
        """
        self.rename = False
        self.was_renamed = True

    def to_hash(self):
        """
        Method to set-up the action of generate hash for file.
        """
        self.hash = True
        self.was_hashed = False

    def hashed(self):
        """
        Method to change the status of `to hash` to `hashed` file.
        """
        self.hash = False
        self.was_hashed = True


class FileHashes:
    """
    Class that store file instance digested hashes.
    """

    _cache = CacheDescriptor()
    """
    Descriptor to storage the digested hashes for the file instance.
    """
    related_file_object = None
    """
    Variable to work as shortcut for the current related object for the hashes.
    """

    def __setitem__(self, hasher_name, value):
        """
        Method to set-up values for file hash as dict item.
        This method expects a tuple as value to set-up the hash hexadecimal value and hash file related
        to the hasher.
        """
        hex_value, hash_file = value

        if not isinstance(hash_file, File):
            raise ImproperlyConfiguredFile("Tuple for hashes must be the Hexadecimal value and a File Object for the "
                                           "hash.")

        self._cache[hasher_name] = hex_value, hash_file

    def __getitem__(self, hasher_name):
        """
        Method to get the hasher value and file associated saved in self._cache.
        """
        return self._cache[hasher_name]

    def __iter__(self):
        """
        Method to return iterable from self._cache instead of current class.
        """
        return iter(self._cache)

    def rename(self, new_filename):
        """
        This method will rename file for each hash file existing in _caches.
        This method don`t save files, only prepare the filename and content to be correct before saving it.
        """
        for hasher_name, value in self._cache.items():
            hex_value, hash_file = value

            if not hash_file._meta.checksum:
                # Rename filename if is not `checksum.hasher_name`
                # complete_filename is a property that will set-up additional action to rename the file`s filename if
                # it was already saved before.
                hash_file.complete_filename = new_filename, hasher_name

            # Load content from generator.
            # First we set-up content of type binary or string.
            content = b"" if hash_file.is_binary else ""

            # Then we load content from generator using a loop.
            for block in hash_file.content:
                content += block

            # Change file`s filename inside content of hash file.
            content = content.replace(f"{hash_file.filename}.{hasher_name}", f"{new_filename}.{hasher_name}")

            # Set-up new content after renaming and specify that hash_file was not saved yet.
            hash_file.content = content
            hash_file._actions.to_save()

    def save(self, overwrite=False):
        """
        Method to save all hashes files if it was not saved already.
        """
        if not self.related_file_object:
            raise ImproperlyConfiguredFile("A related file object must be specified for hashes before saving.")

        for hex_value, hash_file in self._cache.values():
            if hash_file._actions.save:
                if hash_file._meta.checksum:
                    # If file is CHECKSUM.<hasher_name> we not allow overwrite.
                    hash_file.save(overwrite=False, allow_update=overwrite)
                else:
                    hash_file.save(overwrite=overwrite, allow_update=overwrite)


class FileNaming:
    """
    Class that store file instance filenames and related names content.
    """

    reserved_filenames = {}
    """
    Dict of reserved filenames so that the correct file can be renamed
    avoiding overwriting a new file that has the same name as the current file in given directory.
    {<directory>: {<current_filename>: <base_file_object>}}
    """
    reserved_index = {}
    """
    Dict of reference of reserved filenames so that a filename can be easly removed from `reserved_filenames` dict.
    {<filename>: {<base_file_object>: <reference to reserved_index[filename][base_file_object]>}}}
    """

    history = None
    """
    Storage filenames to allow browsing old ones for current BaseFile.
    """
    on_conflict_rename = False
    """
    Option that control behavior of renaming filename.  
    """
    related_file_object = None
    """
    Variable to work as shortcut for the current related object for the hashes.
    """
    previous_saved_extension = None
    """
    Storage the previous saved extension to allow `save` method of file to verify if its changing its `extension`. 
    """

    def remove_reserved_filename(self, old_filename):
        """
        This method remove old filename from list of reserved filenames.
        """

        files = self.reserved_index.get(old_filename, {})
        reference = files.get(self.related_file_object, None)

        # Remove from `reserved_filename` and current `reserved_index`.
        if reference:
            del reference[old_filename]
            del files[self.related_file_object]

    def rename(self):
        """
        Method to rename `related_file_object` according to its own rename pipeline.
        TODO: Change how this method used `reserved_filenames` to allow moving or copying of file.
        """
        save_to = self.related_file_object.save_to
        complete_filename = self.related_file_object.complete_filename

        reserved_folder = self.reserved_filenames.get(save_to, None)
        object_reserved = reserved_folder.get(complete_filename, None) if reserved_folder else None

        # Check if filename already reserved name. Reserved names cannot be renamed even if overwrite is used in save,
        # so the only option is the have a new filename created, but only if `on_conflict_rename` is `True`.
        if reserved_folder and object_reserved and object_reserved is not self.related_file_object:
            if not self.on_conflict_rename:
                raise ReservedFilenameError(f"Rename cannot be made, because the filename {complete_filename} is "
                                            f"already reserved for object {object_reserved} and not for "
                                            f"{self.related_file_object}!")
            else:
                # Prepare reserved names to be set-up in `rename_pipeline`
                reserved_names = [filename for filename in reserved_folder.keys()]

                # Generate new name based on file_system and reserved names calling the rename_pipeline.
                # The pipeline will update `complete_filename` of file to reflect new one. We shouldn`t change `path`
                # of file; `complete_filename` will add the new filename to `history` and remove the old one from
                # `reserved_filenames`.
                self.related_file_object.rename_pipeline.run(
                    object=self.related_file_object,
                    path_attribute='save_to',
                    reserved_names=reserved_names
                )

                # Rename hash_files if there is any. This method not save the hash files giving the responsibility to
                # `save` method.
                self.related_file_object.hashes.rename(self.related_file_object.complete_filename)

        # Update reserved dictionary to reserve current filename.
        if not reserved_folder:
            self.reserved_filenames[save_to] = {complete_filename: self.related_file_object}
        elif not object_reserved:
            self.reserved_filenames[save_to][complete_filename] = self.related_file_object

        # Update reserved index to current filename. This allow for easy finding of filename and object at
        # `self.reserved_filenames`.
        if complete_filename not in self.reserved_index:
            # Pass reference of dict `save_to` to index of reserved names.
            self.reserved_index[complete_filename] = {self: self.reserved_filenames[save_to]}
        else:
            self.reserved_index[complete_filename][self] = self.reserved_filenames[save_to]


class FileContent:
    """
    Class that store file instance content.
    """
    # Properties
    is_binary = False
    """
    Type of stream used in buffer for content. 
    """
    is_internal_content = False
    """
    
    """

    # Buffer handles
    buffer = None
    """
    Stream for file`s content.
    """
    related_file_object = None
    """
    Variable to work as shortcut for the current related object for the hashes.
    """
    _block_size = 256
    """
    Block size of file to be loaded in each step of iterator.
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
    of `_cached_buffer`.
    """
    _cached_buffer = None
    """
    Stream for file`s content cached.
    """

    def __init__(self, raw_value, force=False):
        """
        Initial method that set-up the buffer to be used.
        The parameter `force` when True will force usage of cache even if is IO is seekable.
        """
        if not raw_value:
            raise ValueError(f"Value pass to FileContent must not be empty!")

        if isinstance(raw_value, (str, bytes)):
            try:
                raw_value = StringIO(raw_value)
            except TypeError:
                raw_value = BytesIO(raw_value)

        elif not isinstance(raw_value, IOBase):
            raise ValueError(f"parameter `value` informed in FileContent is not a valid type"
                             f" {type(raw_value)}! We were expecting str, bytes or IOBase.")

        # Set attribute is_binary based on instance type.
        self.is_binary = isinstance(raw_value, BytesIO)

        # Add content (or content converted to Stream) as buffer
        self.buffer = raw_value

        # Set content to be cached.
        if not self.buffer.seekable() or force:
            self.cache_content = True
            self.cached = False

    def __iter__(self):
        """

        """
        return iter(self.generator)

    def __next__(self):
        """

        """
        try:
            content = next(self.__iter__())

            # Cache content
            if self.cache_content:
                # Cache content in memory only
                if self.cache_in_memory:
                    if self._cached_buffer is None:
                        self._cached_buffer = content
                    else:
                        self._cached_buffer += content
                # Cache content in temporary file
                elif self.cache_in_file:
                    pass

            return content

        except StopIteration as e:
            # Change buffer to be cached content
            if self.cache_content and not self.cached:
                class_name = BytesIO if self.is_binary else StringIO
                self.buffer = class_name(self._cached_buffer)

            # Reset buffer to begin from first position
            if self.buffer.seekable():
                self.buffer.seek(0)

            # Create a new generator to use
            self.generator = self.set_generator()
            raise e

    def set_generator(self):
        """
        Generator method to load from buffer IO.
        """
        # Read content in blocks until end of file and return blocks as iterable elements
        while True:
            block = self.buffer.read(self._block_size)

            # This end the loop if block is None, b'' or ''.
            if not block and block != 0:
                break

            yield block


class FileInternalContent(FileContent):
    _content_list = None

    def get_internal_content(self):
        raise NoInternalContentError(f"This file {repr(self)} don't have a internal content.")


class BaseFile:
    """
    Base class for handle File. This class will be used in Files of type Image, Rar, etc.
    This class will behave like Django Model with methods save(), delete(), etc.

    TODO: Add support to moving and copying file avoiding conflict on moving or copying.
    TODO: Add support to packed files and its internal content.
    """

    # Filesystem data
    id = None
    """
    File`s id in the File System.
    """
    filename = None
    """
    Name of file without extension.
    """
    extension = None
    """
    Extension of file.
    """
    create_date = None
    """
    Datetime when file was created.
    """
    update_date = None
    """
    Datetime when file was updated.
    """
    _path = None
    """
    Full path to file including filename. This is the raw path partially sanitized.
    BaseFile.sanitize_path is available through property.
    """
    _save_to = None
    """
    Path of directory to save file. This path will be use for mixing relative paths.
    This path should be accessible through property `save_to`.
    """
    relative_path = None
    """
    Relative path to save file. This path will be use for generating whole path together with save_to and 
    complete_filename (e.g save_to + relative_path + complete_filename). 
    """

    # Metadata data
    length = 0
    """
    Size of file content.
    """
    mime_type = None
    """
    File`s mime type.
    """
    type = None
    """
    File's type (e.g. image, audio, video, application).
    """
    _meta = None
    """
    Additional metadata info that file can have. Those data not always will exist for all files.
    """
    hashes = None
    """
    Checksum information for file.
    It can be multiples like MD5, SHA128, SHA256, SHA512.
    """

    # Initializer data
    _keyword_arguments = None
    """
    Additional attributes data passed to `__init__` method. This information is important to be able to 
    reload data from disk correctly.
    """

    # Handler
    linux_file_system_handler = LinuxFileSystem
    """
    FileSystem for Linux.
    """
    windows_file_system_handler = WindowsFileSystem
    """
    FileSystem for Windows.
    """
    file_system_handler = None
    """
    FileSystem currently in use for File.
    It can be LinuxFileSystem, WindowsFileSystem or a custom one.
    """
    mime_type_handler = LibraryMimeTyper()
    """
    Mimetype handler that defines the source of know Mimetypes.
    This is used to identify mimetype from extension and vice-verse.
    """
    uri_handler = URI
    """
    URI handler that defines methods to parser the URL.
    """

    # Pipelines
    extract_data_pipeline = None
    """
    Pipeline to extract data from multiple sources. This should be override at child class.
    """
    compare_pipeline = Pipeline(
        TypeCompare.to_processor(stopper=True, stop_value=False),
        SizeCompare.to_processor(stopper=True, stop_value=False),
        BinaryCompare.to_processor(stopper=True, stop_value=False),
        HashCompare.to_processor(stopper=True, stop_value=(True, False)),
        DataCompare.to_processor(stopper=True, stop_value=(True, False))
    )
    """
    Pipeline to compare two files.
    """
    hasher_pipeline = Pipeline(
        MD5Hasher.to_processor(),
        SHA256Hasher.to_processor()
    )
    """
    Pipeline to generate hashes from content.
    """
    rename_pipeline = Pipeline(
        WindowsRenamer.to_processor(stopper=True)
    )
    """
    Pipeline to rename file when saving.
    """

    # Behavior controller for file
    _state = None
    """
    Controller for state of file. The file will be set-up with default state before being loaded or create from stream.
    """
    _actions = None
    """
    Controller for pending actions that file must run. The file will be set-up with default (empty) actions.
    """
    _naming = None
    """
    Controller for renaming restrictions that file must adopt.
    """
    _content = None
    """
    Controller for how the content of file will be handled. 
    """

    # Common Exceptions shortcut
    ImproperlyConfiguredFile = ImproperlyConfiguredFile
    """
    Exception to throw when a required configuration is missing or misplaced.
    """
    ValidationError = ValidationError
    """
    Exception to throw when a required attribute to be save is missing or improperly configured.
    """
    OperationNotAllowed = OperationNotAllowed
    """
    Exception to throw when a operation is no allowed to be performed due to how the options are set-up in `save` 
    method.
    """
    NoInternalContentError = NoInternalContentError
    """
    Exception to throw when file was no internal content or being of wrong type to have internal content.
    """
    ReservedFilenameError = ReservedFilenameError
    """
    Exception to throw when a file is trying to be renamed, but there is already another file with the filename 
    reserved. 
    """

    def __init__(self, **kwargs):
        """
        Method to instantiate BaseFile. This method can be used for any child class, ony needing
        to change the extract_data_pipeline to be suited for each class.

        Keyword argument `file_system_handler` allow to specified a custom file system handler.
        Keyword argument `extract_data_pipeline` allow to specified a custom file extractor pipeline.
        """
        # Validate class creation
        if self.extract_data_pipeline is None and not 'extract_data_pipeline' in kwargs:
            raise self.ImproperlyConfiguredFile("File object must set-up a pipeline for data`s extraction.")

        # Set-up current file system.
        self.file_system_handler = kwargs.pop('file_system_handler', None)

        if not self.file_system_handler:
            self.file_system_handler = (
                self.windows_file_system_handler
                if name == 'nt'
                else self.linux_file_system_handler
            )

        new_kwargs = {}
        # Set-up attributes from kwargs like `file_system_handler` or `path`
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
            else:
                new_kwargs[key] = value

        self._keyword_arguments = new_kwargs

        # Set-up resources used for `save` and `update` methods.
        self._actions = FileActions()

        # Set-up resources used for controlling the state of file.
        self._state = FileState()

        # Set-up metadata of file
        self._meta = FileMetadata()

        # Set-up resources used for handling hashes and hash files.
        self.hashes = FileHashes()
        self.hashes.related_file_object = self

        # Set-up resources used for filename renaming control.
        self._naming = FileNaming()
        self._naming.history = []
        self._naming.related_file_object = self

        # Process extractor pipeline
        extract_data_pipeline = kwargs.pop('extract_data_pipeline', None)
        if extract_data_pipeline:
            self.extract_data_pipeline = extract_data_pipeline

        self.extract_data_pipeline.run(self, **new_kwargs)

    def __len__(self):
        """
        Method to inform function `len()` where to extract the information of length from.
        When calling `len(BaseFile())` it will return the size of file in bytes.
        """
        return self.length

    def __lt__(self, other_instance):
        """
        Method to allow comparison < to work between BaseFiles.
        TODO: Compare metadata resolution for when type is image, video and bitrate when type
        is audio and sequence when type is chemical.
        """
        # Check if size is lower than.
        return len(self) < len(other_instance)

    def __le__(self, other_instance):
        """
        Method to allow comparison <= to work between BaseFiles.
        """
        return self.__lt__(other_instance) or self.__eq__(other_instance)

    def __eq__(self, other_instance):
        """
        Method to allow comparison == to work between BaseFiles.
        """
        # Run compare pipeline
        try:
            return self.compare_to(other_instance) or False

        except ValueError:
            return False

    def __ne__(self, other_instance):
        """
        Method to allow comparison not equal to work between BaseFiles.
        """
        return not self.__eq__(other_instance)

    def __gt__(self, other_instance):
        """
        Method to allow comparison > to work between BaseFiles.
        TODO: Compare metadata resolution for when type is image, video and bitrate when type
        is audio and sequence when type is chemical.
        """
        # Check if size is greater than.
        return len(self) > len(other_instance)

    def __ge__(self, other_instance):
        """
        Method to allow comparison >= to work between BaseFiles.
        """
        return self.__gt__(other_instance) or self.__eq__(other_instance)

    @property
    def complete_filename(self):
        """
        Method to return as attribute the complete filename from file.
        """
        return self.filename if not self.extension else f"{self.filename}.{self.extension}"

    @complete_filename.setter
    def complete_filename(self, value):
        """
        Method to set complete_filename attribute. For this method
        to work value must be a tuple of <filename, extension>.
        """
        new_filename, new_extension = value

        # Add current values to history
        if self.filename or self.extension:
            if new_filename == self.filename and new_extension == self.extension:
                # Don`t change filename and extension
                return

            # Remove old filename from reserved filenames
            self._naming.remove_reserved_filename(self.complete_filename)

            # Add old filename to history
            self._naming.history.append((self.filename, self.extension))

        # Set-up new filename (only if it is different from previous one).
        self.filename, self.extension = new_filename, new_extension

        # Only set-up renaming of file if it was saved already.
        if not self._state.adding:
            self._actions.to_rename()

    @property
    def content(self):
        """
        Method to return as attribute the content that can be previous loaded from content,
        or a stream_content or need to be load from file system.
        This method can be override in child class and it should always return a generator.
        """
        if not self._content:
            raise ValueError(f"There is no content to use for file {self}.")

        return iter(self._content)

    @content.setter
    def content(self, value):
        """
        Method to set content attribute. This method can be override in child class.
        This method can receive value as string, bytes or buffer.
        """

        # Storage information if content is being loaded to generator for the first time
        loading_content = self._content is None

        try:
            self._content = FileContent(value)

        except ValueError:
            return

        # Update file state to changing only if not adding.
        # Because new content can be changed multiple times, and we not care about
        # how many times it was changed before saving.
        if not self._state.adding and not loading_content:
            self._state.changing = True

        # Update file actions to be saved and hashed.
        self._actions.to_save()
        self._actions.to_hash()

    @property
    def is_binary(self) -> [bool, NoneType]:
        """
        Method to return as attribute if file is binary or not. This information is obtain from `is_binary` from
        `FileContent` that should be set-up when data is loaded to content.

        There is no setter method, because the 'binarility' of file is determined by its content.
        """
        try:
            return self._content.is_binary

        except ValueError:
            return None

    @property
    def path(self):
        """
        Method to return as attribute full path of file.
        """
        return self._path

    @path.setter
    def path(self, value):
        """
        Method to set property attribute path. This method check whether path is a directory before setting, as we only
        allow path to files to be set-up.
        """
        self._path = self.file_system_handler.sanitize_path(value)

        # Validate if path is really a file.
        if self.file_system_handler.is_dir(self._path):
            raise ValueError("Attribute `path` informed for File cannot be a directory.")

    @property
    def save_to(self):
        """
        Method to return as attribute directory where the file should be saved.
        """
        return self._save_to

    @save_to.setter
    def save_to(self, value):
        """
        Method to set property all attributes related to path.
        """
        self._save_to = self.file_system_handler.sanitize_path(value)

        # Validate if path is really a directory.
        if not self.file_system_handler.is_dir(self._save_to):
            raise ValueError("Attribute `save_to` informed for File must be a directory.")

    @property
    def sanitize_path(self):
        """
        Method to return as attribute full sanitized path of file.
        """
        return self.file_system_handler.join(self.save_to, self.relative_path, self.complete_filename)

    def add_valid_filename(self, complete_filename, enforce_mimetype=False) -> bool:
        """
        Method to add filename and extension to file only if it has a valid extension.
        This method return boolean to indicate whether a filename and extension was added or not.

        This method will set the complete filename overridden it if already exists.

        The following attributes are set for file:
        - complete_filename (filename, extension)
        - _meta (compressed, lossless)

        TODO: we could change add_valid_filename to also search for extension
         in mime_type of file, case there is any, for more efficient search
         (currently the search in LibraryMimeTyper() regards of checking extension for mimetype or checking extension
         in all extensions is similar in complexity).
        """
        # Check if there is known extension in complete_filename.
        # This method break extract extension from filename and get check if it is valid, returning
        # extension only if it is registered.
        possible_extension = self.mime_type_handler.guess_extension_from_filename(complete_filename)

        if possible_extension:
            # Enforce use of extension that match mimetype if `enforce_mimetype` is True.
            # This will also override self.extension to use a new one still compatible with mimetype.
            if enforce_mimetype and self.mime_type:
                if possible_extension not in self.mime_type_handler.get_extensions(self.mime_type):
                    return False

            # Use first class Renamer declared in pipeline because `prepare_filename` is a class method from base
            # Renamer class and we don't require any other specialized methods from Renamer children.
            self.complete_filename = self.rename_pipeline[0].prepare_filename(complete_filename, possible_extension)

            # Save additional metadata to file.
            self._meta.compressed = self.mime_type_handler.is_extension_compressed(self.extension)
            self._meta.lossless = self.mime_type_handler.is_extension_lossless(self.extension)

            return True

        return False

    def compare_to(self, *files: tuple):
        """
        Method to run the pipeline, for comparing files.
        This method set-up for current file object with others.
        """
        if not files:
            raise ValueError("There must be at least one file to be compared in `BaseFile.compare_to` method.")

        # Add current object to be compared mixed with others in files before any other
        files.insert(0, self)

        # Run pipeline passing objects to be compared
        self.compare_pipeline.run(objects=files)
        result = self.compare_pipeline.last_result

        if result is None:
            raise ValueError("There is not enough data in files for comparison at `File.compare_to`.")

        return result

    def generate_hashes(self, force=False):
        """
        Method to run the pipeline, to generate hashes, set-up for the file.
        The parameter `force` will make the pipeline always generate hash from content instead of trying to
        load it from a file when there is one.
        """
        if self._actions.hash:
            # If content is being changed a new hash need to be generated instead of load from hash files.
            try_loading_from_file = False if self._state.changing or force else self._actions.was_saved

            self.hasher_pipeline.run(object=self, try_loading_from_file=try_loading_from_file)

            self._actions.hashed()

    def refresh_from_disk(self):
        """
        This method will reset all attributes, calling the pipeline to extract data again from disk.
        Both the content and metadata will be reload from disk.
        """
        # Set-up pipeline to extract data from.
        pipeline = Pipeline(
            FilenameAndExtensionFromPathExtracter.to_processor(),
            MimeTypeFromFilenameExtracter.to_processor(),
            FileSystemDataExtracter.to_processor(),
            HashFileExtracter.to_processor(),
        )

        # Run the pipeline.
        pipeline.run(object=self, **self._keyword_arguments)

    def save(self, **options):
        """
        Method to save file to file system. In this method we do some validation and verify if file can be saved
        following some options informed through parameter `options`.

        Options available:
        - overwrite (bool) - If file with same filename exists it will be overwritten.
        - save_hashes (bool) - If hash generate for file should also be saved.
        - allow_search_hashes (bool) - Allow hashes to be obtained from hash`s files already saved.
        - allow_update (bool) - If file exists its content will be overwritten.
        - allow_rename (bool) - If renaming a file and a file with the same name exists a new one will be create
        instead of overwriting it.
        - create_backup (bool) - If file exists and its content is being updated the old content will be backup
        before saving.

        This method basically do three things:
        1. Create file and its hashes files (if exists option `overwrite` must be `True`).
        2. Update content if was changed (`allow_update` or `create_backup` must be `True` for this method
        to overwritten the content).
        3. Rename filename and its hashes filenames (if new filename already exists in filesystem, `allow_rename`
        must be `True` for this method to change the renaming state).
        """
        # Validate if file has the correct attributes to be saved, because incomplete BaseFile will not be
        # able to be saved. This should verify if there is name, path and content before saving.
        self.validate()

        # Extract options like `overwrite=bool` file, `save_hashes=False`.
        overwrite = options.pop('overwrite', False)
        save_hashes = options.pop('save_hashes', False)
        allow_search_hashes = options.pop('allow_search_hashes', True)
        allow_update = options.pop('allow_update', True)
        allow_rename = options.pop('allow_rename', False)
        allow_extension_change = options.pop('allow_extension_change', True)
        create_backup = options.pop('create_backup', False)

        # If overwrite is False and file exists a new filename must be created before renaming.
        file_exists = self.file_system_handler.exists(self.sanitize_path)

        # Verify which actions are allowed to perform while saving.
        if self._state.adding and file_exists and not overwrite:
            raise self.OperationNotAllowed("Saving a new file is not allowed when there is a existing one in path "
                                           "and `overwrite` is set to `False`!")

        if not self._state.adding and self._state.changing and not (allow_update or create_backup):
            raise self.OperationNotAllowed("Update a file content is not allowed when there is a existing one in path "
                                           "and `allow_update` and `create_backup` are set to `False`!")

        if self._state.renaming and file_exists and not (allow_rename or overwrite):
            raise self.OperationNotAllowed("Renaming a file is not allowed when there is a existing one in path "
                                           "and `allow_rename` and `overwrite` is set to `False`!")

        # Check if extension is being change, raise exception if it is.
        if (
                self._state.renaming
                and self._naming.previous_saved_extension is not None
                and self._naming.previous_saved_extension != self.extension
                and not allow_extension_change
        ):
            raise self.OperationNotAllowed("Changing a file extension is not allowed when `allow_extension_change` is "
                                           "set to `False`!")

        # Create new filename to avoid overwrite if allow_rename is set to `True`.
        if self._state.renaming:
            self._naming.on_conflict_rename=allow_rename
            self._naming.rename()

        # Copy current file to be .bak before updating content.
        if self._state.changing and create_backup:
            self.file_system_handler.backup(self.sanitize_path)

        # Save file using iterable content if there is content to be saved
        if self._state.adding or self._state.changing:
            self.write_content(self.sanitize_path)

        if save_hashes:
            # Generate hashes, this will only generate hashes if there is a change in content
            # or if it is a new file. If the file was saved before,
            # we will try to find it in a `.<hasher_name>` file instead of generating one.
            self.generate_hashes(force=not allow_search_hashes)
            self.hashes.save(overwrite=True)

        # Get id after saving.
        if not self.id:
            self.id = self.file_system_handler.get_path_id(self.sanitize_path)

        # Update BaseFile internal status and controllers.
        self._actions.saved()
        self._actions.renamed()
        self._state.adding = False
        self._state.changing = False
        self._state.renaming = False
        self._naming.previous_saved_extension = self.extension

    def validate(self):
        """
        Method to validate if minimum attributes of file were set to allow saving.
        TODO: This method should be changed to allow more easy override similar to how Django do with `clean`.
        """
        # Check if there is a filename or extension
        if not self.filename and not self.extension:
            raise self.ValidationError("The attribute `filename` or `extension` must be set for the file!")

        # Raise if not save_to provided.
        if not self.save_to:
            raise self.ValidationError("The attribute `save_to` must be set for the file!")

        # Raise if not content provided.
        if self.content is None:
            raise self.ValidationError("The attribute `content` must be set for the file!")

        # Check if mimetype is compatible with extension
        if self.extension and self.extension not in self.mime_type_handler.get_extensions(self.mime_type):
            raise self.ValidationError("The attribute `extension` is not compatible with the set-up mimetype for the "
                                       "file!")

    def write_content(self, path):
        """
        Method to write content to a given path.
        This method will truncate the file before saving content to it.
        """
        write_mode = 'b' if self.is_binary else 't'

        self.file_system_handler.save_file(path, self.content, file_mode='w', write_mode=write_mode)


class ContentFile(BaseFile):
    # Changing between type of file should be made by controller.

    extract_data_pipeline = Pipeline(
        FilenameFromMetadataExtracter.to_processor(),
        MimeTypeFromFilenameExtracter.to_processor(),
        MimeTypeFromContentExtracter.to_processor(),
        MetadataExtracter.to_processor()
    )
    """
    Pipeline to extract data from multiple sources.
    """


class StreamFile(BaseFile):

    extract_data_pipeline = Pipeline(
        FilenameFromMetadataExtracter.to_processor(),
        FilenameFromURLExtracter.to_processor(),
        MimeTypeFromFilenameExtracter.to_processor(),
        MimeTypeFromContentExtracter.to_processor(),
        MetadataExtracter.to_processor()
    )
    """
    Pipeline to extract data from multiple sources.
    """


class DownloadFile(BaseFile):

    extract_data_pipeline = Pipeline(
        FilenameFromMetadataExtracter.to_processor(),
        FilenameFromURLExtracter.to_processor(),
        MimeTypeFromFilenameExtracter.to_processor(),
        MimeTypeFromContentExtracter.to_processor(),
        MetadataExtracter.to_processor(),
        ContentFromSourceExtracter.to_processor()
    )
    """
    Pipeline to extract data from multiple sources.
    """


class File(BaseFile):

    extract_data_pipeline = Pipeline(
        FilenameAndExtensionFromPathExtracter.to_processor(),
        MimeTypeFromFilenameExtracter.to_processor(),
        FileSystemDataExtracter.to_processor(),
        HashFileExtracter.to_processor(),
    )
    """
    Pipeline to extract data from multiple sources.
    """


    # This save must overwrite file.

    # Stream or content are for downloading files.
