import pytest

from filejacket.pipelines.base import BaseComparer
from filejacket.pipelines.comparer import (
    DataCompare,
    SizeCompare,
    HashCompare,
    LousyNameCompare,
    NameCompare,
    MimeTypeCompare,
    BinaryCompare,
    TypeCompare
)


@pytest.mark.parametrize(
    "package_class",
    [
        BaseComparer,
        DataCompare,
        SizeCompare,
        HashCompare,
        LousyNameCompare,
        NameCompare,
        MimeTypeCompare,
        BinaryCompare,
        TypeCompare
    ]
)
def test_class_for_comparing_has_required_attribute(package_class):
    assert hasattr(package_class, 'prepare_filename')
    assert hasattr(package_class, 'add_reserved_name')
    assert hasattr(package_class, 'clean_reserved_names')
    assert hasattr(package_class, 'register_error')
    assert hasattr(package_class, 'process')
    assert hasattr(package_class, 'is_name_reserved')
    assert hasattr(package_class, 'get_name')


def test_base_class_for_comparing_raise_not_implemented_error_in_some_attributes(request, file_jpg, file_svg):
    with pytest.raises(NotImplementedError):
        BaseComparer.is_the_same(file_1=file_jpg, file_2=file_svg)
