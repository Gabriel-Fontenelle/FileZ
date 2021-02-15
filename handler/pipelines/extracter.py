from calendar import timegm
from datetime import datetime
from time import strptime, mktime

from handler.pipelines import ProcessorMixin


__all__ = [
    'Extracter',
    'FileSystemDataExtracter',
    'FilenameAndExtensionFromPathExtracter',
    'FilenameFromMetadataExtracter',
    'HashFileExtracter',
    'MetadataExtracter',
    'MimeTypeFromFilenameExtracter',
    'FilenameFromURLExtracter',
    'PathFromURLExtracter'
]


class Extracter(ProcessorMixin):
    """
    Base class to be inherent to define class to be used on Extracter pipeline.
    """

    @classmethod
    def extract(cls, file_object, overrider: bool, **kwargs: dict):
        """
        Method to extract the information necessary from a file_object.
        This method must be override in child class.
        """
        raise NotImplementedError("Method extract must be overwritten on child class.")

    @classmethod
    def process(cls, *args, **kwargs):
        """
        Method used to run this class on Processor`s Pipeline for Extracting info from Data.
        This method and to_processor() is not need to extract info outside a pipeline.
        This process method is created exclusively to pipeline for objects inherent from BaseFile.

        The processor for renamer uses only one object that must be settled through first argument
        or through key work `object`.

        """
        object_to_process = kwargs.pop('object', args.pop(0))

        try:
            cls.extract(file_object=object_to_process, *args, **kwargs)
        except (ValueError, IOError):
            return False

        return True


class FilenameAndExtensionFromPathExtracter(Extracter):
    """
    Class that define the extraction of data from `path` defined in file_object.
    """

    @classmethod
    def extract(cls, file_object, overrider: bool, **kwargs: dict):
        """
        Method to extract the filename and extension information from attribute `path` of file_object.

        This method will required that the following attributes be set-up in `file_object`:
        - path

        This method will save data in the following attributes of `file_object`:
        - path (sanitized path)
        - filename
        - extension
        - _meta (compressed, lossless)

        This method make use of overrider.
        """
        if not file_object.path:
            raise ValueError(
                "Attribute `path` must be settled before calling `FilenameAndExtensionFromPathExtracter.extract`."
            )

        # Check if has filename and it can be overwritten
        if not (file_object.filename is None or overrider):
            return

        file_system_handler = file_object.file_system_handler

        # Sanitize path
        file_object.path = file_system_handler.sanitize_path(file_object.path)

        # Get complete filename from path
        complete_filename = file_system_handler.get_filename_from_path(file_object.path)

        # Check if there is any extension in complete_filename
        if '.' in complete_filename:
            # Check if there is known extension in complete_filename

            if file_object.add_valid_filename(complete_filename):
                return

        # No extension registered found, so we set extension as empty.
        file_object.filename = complete_filename
        file_object.extension = ''

        # Set-up save_to and relative_path
        file_object.save_to = file_system_handler.get_directory_from_path(file_object.path)
        # Relative path is empty, because save_to is the whole directory
        file_object.relative_path = ''


class FilenameFromMetadataExtracter(Extracter):
    """
    Class that define the extraction of filename from metadata passed to extract.
    """

    @classmethod
    def extract(cls, file_object, overrider: bool, **kwargs: dict):
        """
        Method to extract the information necessary for a file_object from metadata.
        This method will extract filename from `Content-Disposition` if there is one.
        https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Content-Disposition

        This method will save data in the following attributes of `file_object`:
        - filename
        - extension
        - _meta (compressed, lossless, disposition)

        This method make use of overrider.
        """
        # Check if has filename and it can be overwritten
        if not (file_object.filename is None or overrider):
            return

        try:
            content_disposition = MetadataExtracter.get_content_disposition(kwargs['metadata'])

            if not content_disposition:
                return

            # Save metadata disposition as historic
            file_object.add_metadata('disposition', content_disposition)

            candidates = [
                content.strip()
                for content in content_disposition
                if 'filename' in content
            ]

            if not candidates:
                return

            # Make `filename*=` be priority
            candidates.sort()

            filenames = []

            for candidate in candidates:
                # Get indexes of `"`.
                begin = candidate.index('"') + 1
                end = candidate[begin:].index('"')

                # Get filename with help of those indexes.
                complete_filename = candidate[begin:end]

                # Check if filename has a valid extension
                if '.' in complete_filename and file_object.add_valid_filename(complete_filename):
                    return

                if complete_filename:
                    filenames.append(complete_filename)

            file_object.filename = filenames[0]
            file_object.extension = ""

        except KeyError:
            # kwargs has no parameter metadata
            raise ValueError('Parameter `metadata` must be informed as key argument for '
                             '`FilenameFromMetadataExtracter.extract`.')
        except IndexError:
            # filenames has no index 0, so extension was not set-up either, we just need to return.
            return


class FileSystemDataExtracter(Extracter):

    @classmethod
    def extract(cls, file_object, overrider: bool, **kwargs: dict):
        """
        Method to extract the file system information related a file_object.

        This method will required that the following attributes be set-up in `file_object`:
        - path
        - type

        This method will save data in the following attributes of `file_object`:
        - id
        - length
        - create_date
        - update_date
        - content

        This method not make use of overrider. It always override data.
        """

        def generate_content(path, mode):
            """
            Internal function to return a generator for reading the file's content through the file system.
            """
            with file_object.file_system_handler.open_file(path, mode=mode) as f:

                while True:
                    block = f.read(file_object._block_size)

                    if block is None or block is b'':
                        break

                    yield block

        if not file_object.path:
            raise ValueError("Attribute `path` must be settled before calling `FileSystemDataExtracter.extract`.")

        if not file_object.type:
            raise ValueError("Attribute `type` must be settled before calling `FileSystemDataExtracter.extract`.")

        file_system_handler = file_object.file_system_handler

        # Check if path exists
        if not file_system_handler.exists(file_object.path):
            raise IOError("There is no file following attribute `path` in the file system.")

        # Check if path is directory, it should not be
        if file_system_handler.is_dir(file_object.path):
            raise ValueError("Attribute `path` in `file_object` must be a file not directory.")

        # Get path id
        file_object.id = file_system_handler.get_path_id(file_object.path)

        # Get path size
        file_object.length = file_system_handler.get_size(file_object.path)

        # Get created date
        file_object.create_date = file_system_handler.get_created_date(file_object.path)

        # Get last modified date
        file_object.update_date = file_system_handler.get_modified_date(file_object.path)

        # Define mode from file type
        mode = 'r'

        if file_object.type != 'text':
            mode += 'b'

        file_object.is_binary = file_object.type != 'text'

        # Get content generator, same as buffer but without needing to use
        # `.read(),` just loop through chunks of content.
        file_object.content = generate_content(file_object.path, mode)

        # Set-up metadata saved
        file_object.add_metadata(
            'saved',
            True
        )


class HashFileExtracter(Extracter):
    """
    Class that define the extraction of data from hash files for hashers' processors defined in file_object.
    """

    @classmethod
    def extract(cls, file_object, overrider: bool, **kwargs: dict):
        """
        Method to extract the hash information from a hash file related to file_object.

        This method use as kwargs `full_check: bool` that determine if `CHECKSUM` file should
        also be searched.

        This method will required that the following attributes be set-up in `file_object`:
        - path

        This method will save data in the following attributes of `file_object`:
        - hasher

        This method make use of overrider.
        """
        if not file_object.path:
            raise ValueError("Attribute `path` must be settled before calling `HashFileExtracter.extract`.")

        full_check = kwargs.pop('full_check', False)

        for processor in file_object.hasher_pipeline:
            hasher = processor.classname

            if hasher in file_object.hashes and file_object.hashes[hasher] and not overrider:
                continue

            # Extract from hash file and save to hasher if hash file content found.
            hasher.process_from_file(object=file_object, full_check=full_check)


class MimeTypeFromFilenameExtracter(Extracter):
    """
    Class that define the extraction of mimetype data from filename defined in file_object.
    """

    @classmethod
    def extract(cls, file_object, overrider: bool, **kwargs: dict):
        """
        Method to extract the mimetype information from a file_object.

        This method will required that the following attributes be set-up in `file_object`:
        - extension

        This method will save data in the following attributes of `file_object`:
        - mime_type
        - type

        This method make use of overrider.
        """
        # Check if already is a extension and mimetype, if exists do nothing.
        if file_object.mime_type and not overrider:
            return

        # Check if there is a extension for file else is not possible to extract metadata from it.
        if not file_object.extension:
            raise ValueError(
                "Attribute `extension` must be settled before calling `MimeTypeFromFilenameExtracter.extract`."
            )

        # Save in file_object mimetype and type obtained from mime_type_handler.
        file_object.mime_type = file_object.mime_type_handler.get_mimetype(file_object.extension)
        file_object.type = file_object.mime_type_handler.get_type(file_object.mime_type, file_object.extension)


class MetadataExtracter(Extracter):
    """
    Class that define the extraction of multiple file's data from metadata passed to extract.
    """

    @staticmethod
    def get_etag(metadata: dict) -> str:
        """
        Static method to extract ETag from metadata.
        https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Etag
        """
        try:
            etag = metadata['ETag']

            begin = etag.index('"') + 1
            end = etag[begin:].index('"')

            return etag[begin:end]
        except KeyError:
            return ""

    @staticmethod
    def get_mime_type(metadata: dict):
        """
        Static method to extract mimetype from metadata.
        https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Content-Type
        """
        try:
            return metadata['Content-Type'].split(';')[0].strip()

        except (KeyError, IndexError):
            return None

    @staticmethod
    def get_length(metadata: dict) -> int:
        """
        Static method to extract length from metadata.
        https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Content-Length
        """
        try:
            return int(metadata['Content-Length'])
        except KeyError:
            return 0

    @staticmethod
    def get_last_modified(metadata: dict):
        """
        Static method to extract last modified date from metadata.
        https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Last-Modified
        This method is not making use of time zone `%z`.
        """
        try:
            return datetime.fromtimestamp(mktime(strptime(metadata['Last-Modified'], "%a, %d %b %Y %H:%M:%S %z")))
        except KeyError:
            return None

    @staticmethod
    def get_date(metadata: dict):
        """
        Static method to extract creation date from metadata.
        https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Date
        This method is not making use of time zone `%z`.
        This method return the last modified date if no creation date is provided.
        """
        last_modified = MetadataExtracter.get_last_modified(metadata)

        try:
            date = datetime.fromtimestamp(mktime(strptime(metadata['Date'], "%a, %d %b %Y %H:%M:%S %z")))

            # If Last-Modified is lower than Date return Last-Modified
            if last_modified and last_modified < date:
                return last_modified

            return date
        except KeyError:
            return last_modified

    @staticmethod
    def get_content_disposition(metadata: dict) -> list:
        """
        Static method to extract attachment data from metadata.
        https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Content-Disposition
        """
        try:
            return [
                content.strip()
                for content in metadata['Content-Disposition'].split(';')
            ]
        except KeyError:
            return []

    @staticmethod
    def get_expire(metadata: dict):
        """
        Static method to extract the expiration date from metadata.
        https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Expires
        """
        try:
            return datetime.fromtimestamp(mktime(strptime(metadata['Last-Modified'], "%a, %d %b %Y %H:%M:%S %z")))
        except KeyError:
            return None

    @staticmethod
    def get_language(metadata: dict) -> list:
        """
        Method to extract the information of Language from metadata.
        https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Content-Language
        """
        try:
            return [
                content.strip()
                for content in metadata['Content-Language'].split(',')
            ]
        except KeyError:
            return []

    @classmethod
    def extract(cls, file_object, overrider: bool, **kwargs: dict):
        """
        Method to extract the information necessary from a file_object.
        Content-MD5 was deprecated from HTTP because it not allow partial testing.

        This method will required that the following attributes be set-up as kwargs:
        - metadata

        This method not require any previously save data in `file_object`.

        This method will save data in the following attributes of `file_object`:
        - id
        - mime_type
        - extension
        - type
        - create_date
        - update_date
        - _meta (expire, language)

        This method make use of overrider.
        """
        try:
            meta = kwargs['metadata']

            if not meta:
                raise ValueError('Parameter `metadata` must be have value to be extract at '
                                 '`MetadataExtracter.extract`.')

            # Set-up id from Etag
            etag = cls.get_etag(meta)

            if etag and (not file_object.id or overrider):
                file_object.id = etag

            # Set-up mimetype from metadata
            mimetype = cls.get_mime_type(meta)
            if mimetype and (not file_object.mime_type or overrider):
                # Get mimetype
                file_object.mime_type = mimetype

            # Set-up extension from mimetype
            if mimetype and (not file_object.extension or overrider):
                # Get extensions from mimetype, only if mimetype is not stream (because it don't have a extension
                # associated with stream), and if there is no one valid don't register one.
                # In order to avoid wrong extension being settled is recommend to use a Extractor of
                # `FilenameFromURLExtracter` and `FilenameFromMetadataExtracter` before this processor.
                if 'stream' not in mimetype:
                    possible_extension = file_object.mime_type_handler.guess_extension_from_mimetype(mimetype)

                    if possible_extension:
                        file_object.extension = possible_extension

                        # Save additional metadata to file.
                        file_object.add_metadata(
                            'compressed',
                            file_object.mime_type_handler.is_extension_compressed(file_object.extension)
                        )
                        file_object.add_metadata(
                            'lossless',
                            file_object.mime_type_handler.is_extension_lossless(file_object.extension)
                        )

            # Set-up type from mimetype and extension
            if file_object.mime_type and file_object.extension and (not file_object.type or overrider):
                file_object.type = file_object.mime_type_handler.get_type(file_object.mime_type, file_object.extension)
                file_object.is_binary = file_object.type != 'text'

            # Set-up created date from metadata
            create_date = cls.get_date(meta)
            if create_date and (not file_object.create_date or overrider):
                file_object.create_date = create_date

            # Set-up updated date from metadata
            update_date = cls.get_last_modified(meta)
            if update_date and (not file_object.update_date or overrider):
                file_object.update_date = update_date

            # Set-up length from metadata
            length = cls.get_length(meta)
            if length and (not file_object.length or overrider):
                file_object.length = length

            # Set-up language metadata from metadata
            language = cls.get_language(meta)
            if language and (not file_object.has_metadata('language') or overrider):
                file_object.add_metadata(
                    'language',
                    language
                )

            # Set-up expiration date
            expire_date = cls.get_expire(meta)
            if expire_date and (not file_object.has_metadata('expire') or overrider):
                file_object.add_metadata(
                    'expire',
                    expire_date
                )

        except KeyError:
            raise ValueError('Parameter `metadata` must be informed as key argument for '
                             '`MetadataExtracter.extract`.')


class FilenameFromURLExtracter(Extracter):
    """
    Class that define the extraction of complete_filename from URL passed to Extracter Pipeline.
    """

    @classmethod
    def extract(cls, file_object, overrider: bool, **kwargs: dict):
        """
        Method to extract the filename from an URL. The priority will be finding a filename with a
        registered extension, not founding it will use the last one available.

        This method assumes that `url` is already unquoted.

        This method not enforce limit of size for filename or path.

        This method not require any previously save data in `file_object`.

        This method will save data in the following attributes of `file_object`:
        - complete_filename
        - filename
        - extension
        - relative_path

        This method make use of overrider.
        """
        if file_object.filename and not overrider:
            return

        try:
            possible_urls = kwargs['url']
            processed_uri = None
            results = file_object.uri_handler.get_filenames(possible_urls, file_object.file_system_handler)

            if not results:
                return

            # Modify list to also include boolean value to enforce_mimetype or not.
            results = [(result, True) for result in results] + [(result, False) for result in results]

            # Loop through paths to use only the one with valid extension
            # The first part of the loop enforce mimetype, second not enforce mimetype.
            for result, enforce_mimetype in results:
                # Check and set-up filename
                if (result.filename and file_object.add_valid_filename(result.filename,
                                                                       enforce_mimetype=enforce_mimetype)):
                    processed_uri = result.processed_uri
                    break

            if not processed_uri:
                # Filename without valid extension, so we
                # set it as complete_filename the last one.
                # There will be no additional metadata `compressed` and `lossless`.
                file_object.complete_filename = results[-1].filename.rsplit('.', 1)
                processed_uri = results[-1].processed_uri

            # Set-up relative path
            if not file_object.relative_path or overrider:
                cache = file_object.uri_handler.get_processed_uri(processed_uri)
                file_object.relative_path = cache.directory

        except KeyError:
            raise ValueError('Parameter `url` must be informed as key argument for '
                             '`FilenameFromURLExtracter.extract`.')


class PathFromURLExtracter(Extracter):
    """
    Class that define the extraction of relative_path and complete_filename from URL.
    Its recommend to use this Processor after FilenameFromURLExtracter, else it will not be guarantee that
    the path and filename has the same source or that filename is a valid one.
    """

    @classmethod
    def extract(cls, file_object, overrider: bool, **kwargs: dict):
        """
        Method to extract the information necessary from an URL.
        This method will return the last relative_path found with a filename, regardless of having a valid extension
        said filename.

        This method not enforce limit of size for path.

        This method not require any previously save data in `file_object`.

        This method will save data in the following attributes of `file_object`:
        - complete_filename
        - relative_path

        This method make use of overrider, but it don't override filename.
        """
        if file_object.relative_path and not overrider:
            return

        try:
            possible_urls = kwargs['url']

            paths = file_object.uri_handler.get_paths(possible_urls, file_object.file_system_handler)

            if not paths:
                return

            for path in reversed(paths):
                cache = file_object.uri_handler.get_processed_uri(path.processed_uri)
                if cache and cache.filename:
                    file_object.relative_path = path.directory

                    if not file_object.filename:
                        file_object.complete_filename = cache.filename.rsplit('.', 1)

                    return

            # One or multiple path (without valid filename), so we
            # set it as relative_path the last one.
            file_object.relative_path = paths[-1].directory

        except KeyError:
            raise ValueError('Parameter `url` must be informed as key argument for '
                             '`PathFromURLExtracter.extract`.')


class InternalFilesExtracter(Extracter):

    @classmethod
    def extract(cls, file_object, overrider: bool, **kwargs: dict):
        """
        Method to extract the information necessary from a file_object.
        """
        pass


class MimeTypeFromContentExtracter(Extracter):

    @classmethod
    def extract(cls, file_object, overrider: bool, **kwargs: dict):
        """
        Method to extract the information necessary from a file_object.
        This method must be override in child class.
        """
        # Check if already is a extension and mimetype, if exists do nothing.

        # Check if there is a content in file_object, else is not possible to extract the mimetype and extension from
        # it.

        # Check if there is a possible extension and mimetype from content

        # Save in file_object extension and mimetype
        pass





class ContentFromSourceExtracter(Extracter):

    @classmethod
    def extract(cls, file_object, overrider: bool, **kwargs: dict):
        """
        Method to extract the information necessary from a source object.
        """
        source = kwargs.get('source')

        # length

        # content

        # metadata


class ContentExtracter():
    pass
    # Guess extension from content
    # Guess mimetype from content
    # Get size from content
