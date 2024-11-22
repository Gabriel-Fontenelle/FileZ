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

import logging
from typing import Any, Type, TYPE_CHECKING, Iterator, Sequence, Pattern
from io import BytesIO, StringIO

# core modules
from . import Pipeline

# modules
from ..engines.storage import StorageEngine
from ..exception import (
    ImproperlyConfiguredFile,
    MultipleFileExistError,
    ValidationError,
)


if TYPE_CHECKING:
    from ..file import BaseFile


__all__ = [
    "BaseComparer",
    "BaseExtractor",
    "BaseHasher",
    "BaseRenamer",
]


class BaseComparer:
    """
    Base class to be inherent to define classes for use on Comparer pipeline.
    """

    stopper: bool = True
    """
    Variable that define if this class used as processor should stop the pipeline.
    """

    @classmethod
    def is_the_same(cls, file_1: BaseFile, file_2: BaseFile) -> None | bool:
        """
        Method used to check if two files are the same in memory using the File object.
        This method must be overwrite on child class to work correctly.
        """
        raise NotImplementedError(
            "The method is_the_same needs to be overwrite on child class."
        )

    @classmethod
    def process(cls, **kwargs: Any) -> None | bool:
        """
        Method used to run this class on Processor`s Pipeline for Files.
        This method and to_processor() is not need to compare files outside a pipeline.
        This process method is created exclusively to pipeline for objects inherent from BaseFile.

        The processor for comparer uses only one list of objects that must be settled through first argument
        or through key work `objects`.

        This processor return boolean whether files are the same, different of others processors that return boolean
        to indicate that process was ran successfully.
        """
        object_to_process: BaseFile = kwargs.pop("object_to_process")
        objects_to_compare: list | tuple = kwargs.pop("objects_to_compare")

        if not objects_to_compare or not isinstance(objects_to_compare, (list, tuple)):
            raise ValueError(
                "There must be at least one object to compare at `objects_to_compare`s kwargs for "
                "`BaseComparer.process`."
            )

        for element in objects_to_compare:
            is_the_same = cls.is_the_same(object_to_process, element)
            if not is_the_same:
                # This can return None or False
                return is_the_same

        return True


class BaseExtractor:
    """
    Base class to be inherent to define class to be used on Extractor pipeline.
    """

    @classmethod
    def extract(
        cls, file_object: BaseFile, overrider: bool, **kwargs: Any
    ) -> None | bool:
        """
        Method to extract the information necessary from a file_object.
        This method must be override in child class.
        """
        raise NotImplementedError("Method extract must be overwritten on child class.")

    @classmethod
    def process(cls, **kwargs: Any) -> bool:
        """
        Method used to run this class on Processor`s Pipeline for Extracting info from Data.
        This method and to_processor() is not need to extract info outside a pipeline.
        This process method is created exclusively to pipeline for objects inherent from BaseFile.

        This method can throw ValueError and IOError when trying to extract data from content.
        The `Pipeline.run` method will catch those errors.
        """
        object_to_process: BaseFile = kwargs.pop("object_to_process")
        # Pipeline argument has priority for overrider configuration.
        overrider: bool = kwargs.pop(
            "overrider", object_to_process._option.allow_override
        )

        cls.extract(file_object=object_to_process, overrider=overrider, **kwargs)

        return True


class BaseHasher:
    """
    Base class to be inherent to define class to be used on Hasher pipelines.
    """

    file_system_handler: Type[StorageEngine] = StorageEngine
    """
    File System Handler currently in use by class.
    """
    hasher_name: str
    hasher_name = None
    """
    Name of hasher algorithm and also its extension abbreviation.
    """
    hash_objects: dict = {}
    """
    Cache of hashes for given objects' ids.
    """
    hash_digested_values: dict = {}
    """
    Cache of digested hashes for given objects filename.
    """

    @classmethod
    def check_hash(cls, **kwargs: Any) -> bool | None:
        """
        Method to verify integrity of file checking if hash save in file object is the same
        that is generated from file content. File content can be from File System, Memory or Stream
        so it is susceptible to data corruption.
        """
        object_to_process: BaseFile = kwargs.pop("object_to_process")
        hex_value: str = (
            kwargs.pop("compare_to_hex", None)
            or object_to_process.hashes[cls.hasher_name][0]
        )

        hash_instance: Any = cls.instantiate_hash()

        content_iterator: Iterator[
            Sequence[object]
        ] | None = object_to_process.content_as_iterator

        if content_iterator is None:
            return None

        cls.generate_hash(
            hash_instance=hash_instance,
            content_iterator=content_iterator,
            encoding=object_to_process._content.buffer_helper.encoding,
        )
        digested_hex_value: str = cls.digest_hex_hash(hash_instance=hash_instance)

        # Change to lower case to make comparing of hashes case insensitive.
        return digested_hex_value.lower() == hex_value.lower()

    @classmethod
    def digest_hash(cls, hash_instance: Any) -> str:
        """
        Method to digest the hash generated at hash_instance.
        """
        return hash_instance.digest()

    @classmethod
    def digest_hex_hash(cls, hash_instance: Any) -> str:
        """
        Method to digest the hash generated at hash_instance.
        """
        return hash_instance.hexdigest()

    @classmethod
    def get_hash_objects(cls) -> dict:
        """
        Method to get the `hash_object` filtering the `hasher_name` considering that `hash_objects` is a dictionary
        shared between all classes that inherent from `BaseHasher`.
        """
        hash_object: dict = cls.hash_objects.get(cls.hasher_name, {})
        cls.hash_objects[cls.hasher_name] = hash_object

        return hash_object

    @classmethod
    def get_hash_instance(cls, file_id: str) -> Any:
        """
        Method to get the cached instantiate hash object for the given file id.
        """
        try:
            return cls.hash_objects[cls.hasher_name][file_id]
        except KeyError:
            h: Any = cls.instantiate_hash()
            if cls.hasher_name in cls.hash_objects:
                cls.hash_objects[cls.hasher_name][file_id] = h
            else:
                cls.hash_objects[cls.hasher_name] = {file_id: h}

            return h

    @classmethod
    def update_hash(
        cls, hash_instance: Any, content: str | bytes, encoding: str = "utf-8"
    ) -> None:
        """
        Method to update content in hash_instance to generate the hash. We convert all content to bytes to
        generate a hash of it.
        """
        if isinstance(content, str):
            content = content.encode(encoding)

        hash_instance.update(content)

    @classmethod
    def instantiate_hash(cls) -> Any:
        """
        Method to instantiate the hash generator to be used digesting the hash.
        """
        raise NotImplementedError(
            "Method instantiate_hash must be overwrite on child class."
        )

    @classmethod
    def generate_hash(
        cls,
        hash_instance: Any,
        content_iterator: Iterator[Sequence[bytes | str]],
        encoding: str = "utf-8",
    ) -> None:
        """
        Method to update the hash to be generated from content in blocks using a normalized content that can be
        iterated regardless from its source (e.g. file system, memory, stream).
        """
        for block in content_iterator:
            cls.update_hash(hash_instance, block, encoding)

    @classmethod
    def create_hash_file(
        cls, object_to_process: BaseFile, digested_hex_value: str
    ) -> BaseFile:
        """
        Method to create a file structured for the hash based on same class as object_to_process
        """
        if object_to_process.save_to is None or not object_to_process.complete_filename:
            raise ImproperlyConfiguredFile(
                "Generating a hash file for a file without a directory set at `save_to`"
                " and without a `complete_filename` is not supported."
            )

        # Add hash to file
        hash_file: BaseFile = object_to_process.__class__(
            path=f"{cls.file_system_handler.sanitize_path(object_to_process.save_to)}"
            f"{cls.file_system_handler.sep}{object_to_process.complete_filename}.{cls.hasher_name}",
            extract_data_pipeline=Pipeline(
                "filejacket.pipelines.extractor.FilenameAndExtensionFromPathExtractor",
                "filejacket.pipelines.extractor.MimeTypeFromFilenameExtractor",
            ),
            file_system_handler=object_to_process.storage,
        )
        # Set up metadata checksum as boolean to indicate whether the source
        # of the hash is a CHECKSUM.hasher_name file (contains multiple files) or not.
        hash_file.meta.checksum = False

        # Set up metadata loaded as boolean to indicate whether the source
        # of the hash was loaded from a file or not.
        hash_file.meta.loaded = False

        # Generate content for file
        content: str = f"# Generated by Handler{object_to_process.storage.new_line}"
        content += f"{digested_hex_value}  {object_to_process.complete_filename}{object_to_process.storage.new_line}"
        hash_file.content = content

        # Change hash file state to be saved
        hash_file._actions.to_save()

        return hash_file

    @classmethod
    def load_from_file(
        cls,
        directory_path: str,
        filename: str,
        extension: str | None,
        full_check: bool = False,
        full_loop_check: bool = False,
    ) -> tuple[str, str]:
        """
        Method to find and load the hash value from a file named <filename>.<hasher name> or CHECKSUM.<hasher name>
        or <directory_path>.<hasher_name>.
        Both names will be used if `full_check` is True, else only <filename>.<hasher name> will be searched.
        """

        def generator_join_folder_name(folder_name, iterator):
            for value in iterator:
                yield cls.file_system_handler.join(folder_name, value)

        extension = f".{extension}" if extension else ""
        full_name: str = filename + extension

        # Load and cache dictionary
        hash_digested: dict = cls.hash_digested_values.get(cls.hasher_name, {})
        if not hash_digested:
            # Add missing hasher_name dictionary
            cls.hash_digested_values[cls.hasher_name] = hash_digested

        hash_directories: dict = hash_digested.get(full_name, {})
        if not hash_directories:
            cls.hash_digested_values[cls.hasher_name][full_name] = hash_directories

        # Return cached hash if already processed.
        if directory_path in hash_directories:
            return hash_directories[directory_path]

        files_to_check: list[str] = [
            # Check checksum files that contain the full name of file plus `cls.hasher_name`
            cls.file_system_handler.join(
                directory_path, full_name + "." + cls.hasher_name
            ),
            # Check checksum files that removed the extension from filename plus `cls.hasher_name`.
            cls.file_system_handler.join(
                directory_path, filename + "." + cls.hasher_name
            ),
            # Check checksum files that literally are named `CHECKSUM`.
            cls.file_system_handler.join(directory_path, "CHECKSUM." + cls.hasher_name),
            # Check checksum files that are named after its directory
            cls.file_system_handler.join(
                directory_path,
                cls.file_system_handler.get_filename_from_path(directory_path)
                + "."
                + cls.hasher_name,
            ),
        ]

        if full_loop_check:
            # Iterate through directory to find all files of type `cls.hasher_name` in order to load all available
            # checksums loop until hash is found or root reached.

            list_checksums = list(
                generator_join_folder_name(
                    directory_path,
                    cls.file_system_handler.list_files(
                        directory_path, f"*.{cls.hasher_name}"
                    ),
                )
            )
            parent = cls.file_system_handler.get_parent_directory_from_path(
                directory_path
            )

            while not list_checksums:
                list_checksums = list(
                    generator_join_folder_name(
                        parent,
                        cls.file_system_handler.list_files(
                            parent, f"*.{cls.hasher_name}"
                        ),
                    )
                )

                new_parent = cls.file_system_handler.get_parent_directory_from_path(
                    parent
                )

                # If root reached break loop
                if new_parent == parent:
                    break

                parent = new_parent

            files_to_check += list_checksums

        elif full_check:
            # Iterate through directory to find all files of type `cls.hasher_name` in order to load all available
            # checksums.
            files_to_check += list(
                generator_join_folder_name(
                    directory_path,
                    cls.file_system_handler.list_files(
                        directory_path, f"*.{cls.hasher_name}"
                    ),
                )
            )

        # Try to find filename with hasher_name in directory_path or
        # try to find filename in CHECKSUM.<hasher_name> in directory_path
        for file_path in set(files_to_check):
            if cls.file_system_handler.exists(file_path):
                # Get relative path from file_path to allow search of directory and not only full_name in line.

                candidates = []

                for line in cls.file_system_handler.read_lines(file_path):
                    # We ignore lines that begin with comment describer `;`.
                    full_path: str = (
                        directory_path.replace(
                            cls.file_system_handler.get_directory_from_path(file_path)
                            + cls.file_system_handler.sep,
                            "",
                            1,
                        )
                        + cls.file_system_handler.sep
                        + full_name
                    )

                    if ";" != line[0] and "#" != line[0]:
                        if full_path in line:
                            # Get hash from line and return it.
                            # It's assuming that first argument until first white space if the hash and second
                            # is the filename.
                            hashed_value: str = line.lstrip().split(maxsplit=1)[0]

                            # Add hash to cache
                            hash_directories[directory_path] = hashed_value, file_path

                            return hashed_value, file_path

                        elif full_name in line:
                            # Get hash from line and return it.
                            # It's assuming that first argument until first white space if the hash and second
                            # is the filename.
                            hashed_value: str = line.lstrip().split(maxsplit=1)[0]

                            candidates.append((hashed_value, file_path))

                # Case we reach this point no complete file was found, but we can have candidates.
                # If more than one candidate is found
                if len(candidates) > 1:
                    # Check if checksum is the same in all candidates.
                    if len(set([value[0] for value in candidates])) == 1:
                        hash_directories[directory_path] = (
                            candidates[0][0],
                            candidates[0][1],
                        )

                        return candidates[0][0], candidates[0][1]
                    else:
                        raise MultipleFileExistError(
                            f"{full_name} has multiple candidates for {cls.hasher_name} with distinct hashes! Hashes found: {candidates}"
                        )

                elif len(candidates) == 1:
                    # Add hash to cache
                    hash_directories[directory_path] = (
                        candidates[0][0],
                        candidates[0][1],
                    )

                    return candidates[0][0], candidates[0][1]

        raise FileNotFoundError(f"{full_name} not found!")

    @classmethod
    def process(cls, **kwargs: Any) -> bool:
        """
        Method used to run this class on Processor's Pipeline for Hash.
        This method and to_processor() is not need to generate hash outside a pipelines.
        This process method is created exclusively to pipeline for objects inherent from BaseFile.

        The processor for hasher uses only one object that must be settled through first argument
        or through key work `object`.

        FUTURE CONSIDERATION: Making the pipeline multi thread or multi process will require that iterator of content
        be a isolated copy of content to avoid race condition when using content where its provenience came from file
        pointer.

        This processors return boolean to indicate that process was ran successfully.
        """
        object_to_process: BaseFile = kwargs["object_to_process"]
        try_loading_from_file: bool = kwargs.get("try_loading_from_file", False)

        # Check if there is already a hash previously loaded on file,
        # so that we don't try to digest it again.
        if cls.hasher_name not in object_to_process.hashes:
            if try_loading_from_file:
                # Check if hash loaded from file and if so exit with success.
                if cls.process_from_file(**kwargs):
                    return True

            file_id: str = str(id(object_to_process))

            # Check if there is already a hash previously generated in cache.
            if file_id not in cls.get_hash_objects():
                # Check if there is a content loaded for file before generating a new one
                content = object_to_process.content_as_iterator
                if content is None:
                    return False

                # Get hash_instance
                hash_instance: Any = cls.get_hash_instance(file_id)

                # Generate hash
                cls.generate_hash(
                    hash_instance=hash_instance,
                    content_iterator=content,
                    encoding=object_to_process._content.buffer_helper.encoding,
                )

            else:
                hash_instance = cls.get_hash_objects()[file_id]

            # Digest hash
            digested_hex_value: str = cls.digest_hex_hash(hash_instance=hash_instance)

            # Add hash to file
            hash_file: BaseFile = cls.create_hash_file(
                object_to_process, digested_hex_value
            )

            object_to_process.hashes[cls.hasher_name] = (
                digested_hex_value,
                hash_file,
                cls,
            )

        return True

    @classmethod
    def process_from_file(cls, **kwargs: Any) -> bool:
        """
        Method to try to process the hash from a hash's file instead of generating one.
        It will return False if no hash was found in files.

        Specifying the keyword argument `full_check` as True will make the processor to verify the hash value in file
        CHECKSUM.<cls.hasher_name>, if there is any in the same directory as the file to be processed.
        """
        object_to_process: BaseFile = kwargs.pop("object_to_process")
        full_check: bool = kwargs.pop("full_check", True)
        full_loop_check: bool = kwargs.pop("full_loop_check", False)

        # Save current file system filejacket
        class_file_system_handler: Type[StorageEngine] = cls.file_system_handler

        cls.file_system_handler = object_to_process.storage

        # Don't proceed if no path was setted.
        if not object_to_process.path:
            return False

        path: str = cls.file_system_handler.sanitize_path(object_to_process.path)
        directory_path: str = cls.file_system_handler.get_directory_from_path(path)

        try:
            hex_value, hash_file_path = cls.load_from_file(
                directory_path=directory_path,
                filename=object_to_process.filename,
                extension=object_to_process.extension,
                full_check=full_check,
                full_loop_check=full_loop_check,
            )
        except FileNotFoundError:
            return False
        finally:
            # Restore File System attribute to original.
            cls.file_system_handler = class_file_system_handler

        file_system: Type[StorageEngine] = object_to_process.storage

        # Add hash to file. The content will be obtained from file pointer.
        hash_file: BaseFile = object_to_process.__class__(
            path=hash_file_path,
            extract_data_pipeline=Pipeline(
                "filejacket.pipelines.extractor.FilenameAndExtensionFromPathExtractor",
                "filejacket.pipelines.extractor.MimeTypeFromFilenameExtractor",
                "filejacket.pipelines.extractor.FileSystemDataExtractor",
            ),
            file_system_handler=file_system,
        )
        # Set-up metadata checksum as boolean to indicate whether the source
        # of the hash is a CHECKSUM.hasher_name file (contains multiple files) or not.
        hash_file.meta.checksum = "CHECKSUM." in hash_file_path

        # Set-up metadata loaded as boolean to indicate whether the source
        # of the hash was loaded from a file or not.
        hash_file.meta.loaded = True

        # Change hash file state to be a existing one already saved.
        hash_file._state.adding = False
        hash_file._actions.saved()

        # Set-up the hex value and hash_file to hash content.
        object_to_process.hashes[cls.hasher_name] = hex_value, hash_file, cls

        return True


class BaseRenamer:
    """
    Base class to be inherent to define class to be used on Renamer pipeline.
    """

    stopper: bool = True
    """
    Variable that define if this class used as processor should stop the pipeline.
    """
    file_system_handler: Type[StorageEngine] = StorageEngine
    """
    Variable to store the local storage system.
    """
    enumeration_pattern: Pattern
    enumeration_pattern = None
    """
    Variable that define the pattern to detect enumeration in file system.
    """

    reserved_names: list = []
    """
    Variable that define the reversed names by the file system that should be avoid in renaming.
    """

    @classmethod
    def prepare_filename(
        cls, filename: str, extension: str | None = None
    ) -> tuple[str, str | None]:
        """
        Method to separated extension from filename if extension
        not informed and save on class.
        """
        # Remove extension from filename if it was given
        if extension and filename[-len(extension) :] == extension:
            filename = filename[: -len(f".{extension}")]

        return filename, extension

    @classmethod
    def get_name(
        cls, directory_path: str, filename: str, extension: str | None
    ) -> tuple[str, str | None]:
        """
        Method to get the new generated name.
        This class should raise BlockingIOError when a custom error should happen that will be
        caught by `process` when using Pipeline.
        """
        raise NotImplementedError("Method get_name must be overwrite on child class.")

    @classmethod
    def process(cls, **kwargs: Any) -> bool:
        """
        Method used to run this class on Processor`s Pipeline for Files.
        This method and to_processor() is not need to rename files outside a pipeline.
        This process method is created exclusively to pipeline for objects inherent from BaseFile.

        The processor for renamer uses only one object that must be settled through first argument
        or through key work `object`.

        The keyword argument `path_attribute` allow using a different attribute for specify the file object path other
        than the default `path`.
        The keyword argument `reserved_names` allow for override of current list of reserved_names in pipeline. This
        override will affect the class and thus all usage of `reserved_names`. It isn`t thread safe.

        FUTURE CONSIDERATION: Making the pipeline multi thread or multi process only will required that
        a lock be put between usage of get_name.
        FUTURE CONSIDERATION: Multi thread will need to consider that the attribute `file_system_handler`
        is shared between the reference of the class and all object of it and will have to be change the
        code (multi process don't have this problem).

        This processors return boolean to indicate that process was ran successfully.

        This method can throw BlockingIOError when trying to rename the file.
        The `Pipeline.run` method will catch it.
        """
        # Get default values from keywords arguments
        object_to_process: BaseFile = kwargs.pop("object_to_process")
        path_attribute: str = kwargs.pop("path_attribute", "path")
        reserved_names: list | None = kwargs.pop("reserved_names", None)

        # Override current reserved names if list of new one provided.
        if reserved_names:
            cls.clean_reserved_names()
            cls.add_reserved_name(reserved_names)

        # Prepare filename from File's object
        filename, extension = cls.prepare_filename(
            object_to_process.filename, object_to_process.extension
        )

        # Save current file system filejacket
        class_file_system_handler = cls.file_system_handler

        # Overwrite File System attribute with File System of File only when running in pipeline.
        # This will alter the File System for the class, any other call to this class will use the altered
        # file system.
        cls.file_system_handler = object_to_process.storage

        # Get directory from object to be processed.
        path = cls.file_system_handler.sanitize_path(
            getattr(object_to_process, path_attribute)
        )

        # When is not possible to get new name by some problem either with file or filesystem
        # is expected BlockingIOError
        new_filename, extension = cls.get_name(path, filename, extension)

        # Restore File System attribute to original.
        cls.file_system_handler = class_file_system_handler

        # Set new name at File's object.
        # The File class should set the old name at File`s cache/history automatically,
        # filename and extension should be property functions.
        object_to_process.complete_filename_as_tuple = (new_filename, extension)

        return True

    @classmethod
    def is_name_reserved(cls, filename: str, extension: str) -> bool:
        """
        Method to check if filename in list of reserved names.
        Those name should be set-up before rename pipeline being called.
        """
        return filename + extension in cls.reserved_names

    @classmethod
    def add_reserved_name(cls, value: str | list) -> None:
        """
        Method to update list of reserved names allowing append of multiple values with list.
        This method accept string or list to be added to reserved_names.
        """
        if isinstance(value, str):
            cls.reserved_names.append(value)

        elif isinstance(value, list):
            cls.reserved_names += value

    @classmethod
    def clean_reserved_names(cls) -> None:
        """
        Method to reset the `reserved_names` attribute to a empty list.
        """
        cls.reserved_names = []

    @classmethod
    def register_error(cls, error: Exception) -> None:
        """
        Method to log error in system. It could be override to register error in list or distinct output.
        """
        # Log error message
        logging.error(str(error))


class BaseRender:
    """
    Render class with focus to processing information from file's content to create a representation of it.
    """

    extensions: set[str]
    extensions = None
    """
    Attribute to store allowed extensions for use in `validator`.
    This attribute should be override in children classes.
    """

    stopper: bool = True
    """
    Variable that define if this class used as processor should stop the pipeline.
    """

    @classmethod
    def create_file(
        cls, object_to_process: BaseFile, content: str | bytes | BytesIO | StringIO
    ) -> BaseFile:
        raise NotImplementedError(
            "Method create_file must be overwritten on child class."
        )

    @classmethod
    def process(cls, **kwargs: Any) -> bool:
        """
        Method used to run this class on Processor`s Pipeline for Rendering images from Data.
        This process method is created exclusively to pipeline for objects inherent from BaseFile.

        This method can throw ValueError and IOError when trying to render the content. The `Pipeline.run` method will
        catch those errors.
        """
        object_to_process: BaseFile = kwargs.pop("object_to_process", None)

        try:
            # Validate whether the extension for the current class is compatible with the render.
            cls.validate(file_object=object_to_process)

            # Render the static image for the FileThumbnail.
            cls.render(file_object=object_to_process, **kwargs)

        except ValidationError:
            # We consume and don't register validation error because it is a expected error case the extension is
            # not compatible with the method.
            return False

        return True

    @classmethod
    def render(cls, file_object: BaseFile, **kwargs: Any) -> None:
        """
        Method to render the image representation of the file_object.
        This method must be override in child class.
        """
        raise NotImplementedError("Method render must be overwritten on child class.")

    @classmethod
    def validate(cls, file_object: BaseFile) -> None:
        """
        Method to validate if content can be rendered to given extension.
        """
        if cls.extensions is None:
            raise NotImplementedError(
                f"The attribute extensions is not overwritten in child class {cls.__name__}"
            )

        # The ValidationError should be captured in children classes else it will not register as an error and
        # the pipeline will break.
        if file_object.extension not in cls.extensions:
            raise ValidationError(
                f"Extension {file_object.extension} not allowed in validate for class {cls.__name__}"
            )
