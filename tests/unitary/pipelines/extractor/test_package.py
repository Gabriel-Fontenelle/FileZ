import pytest

from filejacket.pipelines.extractor.package import (
    PackageExtractor,
    PSDLayersFromPackageExtractor,
    SevenZipCompressedFilesFromPackageExtractor,
    RarCompressedFilesFromPackageExtractor,
    TarCompressedFilesFromPackageExtractor,
    ZipCompressedFilesFromPackageExtractor
)


@pytest.mark.parametrize(
    "package_class",
    [
        PackageExtractor,
        PSDLayersFromPackageExtractor,
        TarCompressedFilesFromPackageExtractor,
        ZipCompressedFilesFromPackageExtractor,
        RarCompressedFilesFromPackageExtractor,
        SevenZipCompressedFilesFromPackageExtractor,
    ]
)
def test_class_for_unpacking_has_required_attribute(package_class):
    assert hasattr(package_class, 'validate')
    assert hasattr(package_class, 'decompress')
    assert hasattr(package_class, 'content_buffer')
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
        PackageExtractor.validate(file_object=file_object)

    with pytest.raises(NotImplementedError):
        PackageExtractor.decompress(file_object=file_object, overrider=False)
    
    with pytest.raises(NotImplementedError):
        PackageExtractor.content_buffer(file_object=file_object, internal_file_name="name", mode="rb")
