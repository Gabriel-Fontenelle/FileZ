import pytest

from filejacket.pipelines.extractor.package import (
    PackageExtractor,
    PSDLayersFromPackageExtractor,
    SevenZipCompressedFilesFromPackageExtractor,
    RarCompressedFilesFromPackageExtractor,
    TarCompressedFilesFromPackageExtractor,
    ZipCompressedFilesFromPackageExtractor
)


def test_method_content_buffer():
    
    pass

def test_method_extract():
    
    pass

def test_method_decompress():
    pass


@pytest.mark.parametrize(
    "file_fixture",
    [
        "file_jpg",
        "file_gif",
        "file_rar",
        "file_mp4"
    ],
)
def test_method_validate(request, file_fixture):
    file_object = request.getfixturevalue(file_fixture)
    
    

def test_method_process():
    pass
