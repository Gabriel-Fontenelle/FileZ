import pytest

from filejacket.pipelines.base import (
    BaseExtractor
)
from filejacket.pipelines.extractor import (
    # Content
    AudioMetadataFromContentExtractor,
    DocumentMetadataFromContentExtractor,
    MimeTypeFromContentExtractor,
    VideoMetadataFromContentExtractor,
    # External data
    FileSystemDataExtractor,
    FilenameAndExtensionFromPathExtractor,
    FilenameFromMetadataExtractor,
    HashFileExtractor,
    MetadataExtractor,
    MimeTypeFromFilenameExtractor,
    FilenameFromURLExtractor,
    PathFromURLExtractor
)


@pytest.mark.parametrize(
    "package_class",
    [
        AudioMetadataFromContentExtractor,
        DocumentMetadataFromContentExtractor,
        MimeTypeFromContentExtractor,
        VideoMetadataFromContentExtractor,
        FileSystemDataExtractor,
        FilenameAndExtensionFromPathExtractor,
        FilenameFromMetadataExtractor,
        HashFileExtractor,
        MetadataExtractor,
        MimeTypeFromFilenameExtractor,
        FilenameFromURLExtractor,
        PathFromURLExtractor
    ]
)
def test_class_for_unpacking_has_required_attribute(package_class):
    assert hasattr(package_class, 'extract')
    assert hasattr(package_class, 'process')


@pytest.mark.parametrize(
    "file_fixture",
    [
        "file_jpg",
        "file_gif",
        "file_rar",
        "file_mp4"
    ],
)
def test_base_class_for_unpacking_raise_not_implemented_error_in_some_attributes(request, file_fixture):
    file_object = request.getfixturevalue(file_fixture)
    
    with pytest.raises(NotImplementedError):
        BaseExtractor.extract(file_object=file_object, overrider=False)
