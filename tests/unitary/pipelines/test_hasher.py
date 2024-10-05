import pytest

from filejacket.pipelines.base import BaseHasher
from filejacket.pipelines.hasher import (
    MD5Hasher,
    SHA256Hasher,
    CRC32Hasher,
)


@pytest.mark.parametrize(
    "package_class",
    [
        BaseHasher,
        MD5Hasher,
        SHA256Hasher,
        CRC32Hasher,
    ]
)
def test_class_for_unpacking_has_required_attribute(package_class):
    assert hasattr(package_class, 'check_hash')
    assert hasattr(package_class, 'digest_hash')
    assert hasattr(package_class, 'digest_hex_hash')
    assert hasattr(package_class, 'get_hash_objects')
    assert hasattr(package_class, 'get_hash_instance')
    assert hasattr(package_class, 'update_hash')
    assert hasattr(package_class, 'instantiate_hash')
    assert hasattr(package_class, 'generate_hash')
    assert hasattr(package_class, 'create_hash_file')
    assert hasattr(package_class, 'load_from_file')
    assert hasattr(package_class, 'process')      
    assert hasattr(package_class, 'process_from_file')  


def test_base_class_for_hashing_raise_not_implemented_error_in_some_attributes():
    with pytest.raises(NotImplementedError):
        BaseHasher.instantiate_hash()
