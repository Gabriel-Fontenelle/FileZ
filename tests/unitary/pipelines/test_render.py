import pytest

from filejacket.pipelines.base import BaseRender
from filejacket.pipelines.render import (
    BaseStaticRender,
    DocumentFirstPageRender,
    ImageRender,
    PSDRender,
    VideoRender
)


@pytest.mark.parametrize(
    "package_class",
    [
        BaseRender,
        BaseStaticRender,
        DocumentFirstPageRender,
        ImageRender,
        PSDRender,
        VideoRender
    ]
)
def test_class_for_unpacking_has_required_attribute(package_class):
    assert hasattr(package_class, 'create_file')
    assert hasattr(package_class, 'process')
    assert hasattr(package_class, 'render')
    assert hasattr(package_class, 'validate')


@pytest.mark.parametrize(
    "file_fixture",
    [
        "file_jpg",
        "file_gif",
        "file_rar",
        "file_mp4"
    ],
)
def test_base_class_for_rendering_raise_not_implemented_error_in_some_attributes(request, file_fixture):
    file_object = request.getfixturevalue(file_fixture)
    
    with pytest.raises(NotImplementedError):
        BaseRender.create_file(file_object=file_object, content=b"Test content")

    with pytest.raises(NotImplementedError):
        BaseRender.render(file_object=file_object)
    
    with pytest.raises(NotImplementedError):
        BaseRender.validate(file_object=file_object)
