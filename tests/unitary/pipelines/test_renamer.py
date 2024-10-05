import pytest

from filejacket.pipelines.base import BaseRenamer
from filejacket.pipelines.renamer import (
    WindowsRenamer,
    LinuxRenamer,
    UniqueRenamer,
)


@pytest.mark.parametrize(
    "package_class",
    [
        BaseRenamer,
        WindowsRenamer,
        LinuxRenamer,
        UniqueRenamer,
    ]
)
def test_class_for_unpacking_has_required_attribute(package_class):
    assert hasattr(package_class, 'prepare_filename')
    assert hasattr(package_class, 'add_reserved_name')
    assert hasattr(package_class, 'clean_reserved_names')
    assert hasattr(package_class, 'register_error')
    assert hasattr(package_class, 'process')
    assert hasattr(package_class, 'is_name_reserved')
    assert hasattr(package_class, 'get_name')


def test_base_class_for_renaming_raise_not_implemented_error_in_some_attributes(request, file_fixture):
    with pytest.raises(NotImplementedError):
        BaseRenamer.get_name(directory_path="path", filename="filename", extension="jpg")
