import pytest

from filejacket.file import FileActions


@pytest.fixture
def file_action():
    return FileActions()


def test_class_default_attributes(file_action):
    # Available actions for file object
    assert file_action.save is False
    assert file_action.extract is False
    assert file_action.rename is False
    assert file_action.move is False
    assert file_action.hash is False
    assert file_action.list is False
    assert file_action.preview is False
    assert file_action.thumbnail is False
    
    # Actions performed for file object
    assert file_action.was_saved is False
    assert file_action.was_extracted is False
    assert file_action.was_renamed is False
    assert file_action.was_moved is False
    assert file_action.was_hashed is False
    assert file_action.was_listed is False
    assert file_action.was_previewed is False
    assert file_action.was_thumbnailed is False


@pytest.mark.parametrize(
    "kwargs",
    [
        {"save": True},
        {"save": True, "extract": True},
        {"save": True, "move": True},
        {"was_saved": True, "move": True},
        {"thumbnail": True, "preview": True},
        {"list": True, "hash": True},
        {"was_thumbnailed": True, "was_previewed": True, "was_saved": True},
        {"was_renamed": True, "was_moved": True, "was_hashed": True, "was_listed": True}
    ]
)
def test_class_file_action_method__init___should_set_values_when_informed(kwargs):
    file_action = FileActions(**kwargs)
    for key, value in kwargs.items():
        assert getattr(file_action, key) is value


@pytest.mark.parametrize(
    "kwargs",
    [
        {"save": True},
        {"save": True, "extract": True},
        {"save": True, "move": True},
        {"was_saved": True, "move": True},
        {"thumbnail": True, "preview": True},
        {"list": True, "hash": True},
        {"was_thumbnailed": True, "was_previewed": True, "was_saved": True},
        {"was_renamed": True, "was_moved": True, "was_hashed": True, "was_listed": True}
    ]
)
def test_class_file_action_method__serialize__(kwargs):
    file_action = FileActions(**kwargs)
    
    serialized = file_action.__serialize__
    
    assert serialized == {**{
            "extract": False,
            "hash": False,
            "list": False,
            "move": False,
            "preview": False,
            "rename": False,
            "save": False,
            "thumbnail": False,
            "was_extracted": False,
            "was_hashed": False,
            "was_listed": False,
            "was_moved": False,
            "was_previewed": False,
            "was_renamed": False,
            "was_saved": False,
            "was_thumbnailed": False
        },
        **kwargs
    }


def test_class_file_action_method_to_extract(file_action):
    assert file_action.extract is False
    assert file_action.was_extracted is False
    
    file_action.to_extract()

    assert file_action.extract is True
    assert file_action.was_extracted is False


def test_class_file_action_method_extracted(file_action):
    assert file_action.extract is False
    assert file_action.was_extracted is False
    
    file_action.extracted()

    assert file_action.extract is False
    assert file_action.was_extracted is True


def test_class_file_action_method_to_save(file_action):
    assert file_action.save is False
    assert file_action.was_saved is False
    
    file_action.to_save()

    assert file_action.save is True
    assert file_action.was_saved is False


def test_class_file_action_method_saved(file_action):
    assert file_action.save is False
    assert file_action.was_saved is False
    
    file_action.saved()

    assert file_action.save is False
    assert file_action.was_saved is True


def test_class_file_action_method_to_rename(file_action):
    assert file_action.rename is False
    assert file_action.was_renamed is False
    
    file_action.to_rename()

    assert file_action.rename is True
    assert file_action.was_renamed is False


def test_class_file_action_method_renamed(file_action):
    assert file_action.rename is False
    assert file_action.was_renamed is False
    
    file_action.renamed()

    assert file_action.rename is False
    assert file_action.was_renamed is True


def test_class_file_action_method_to_move(file_action):
    assert file_action.move is False
    assert file_action.was_moved is False
    
    file_action.to_move()

    assert file_action.move is True
    assert file_action.was_moved is False


def test_class_file_action_method_moved(file_action):
    assert file_action.move is False
    assert file_action.was_moved is False
    
    file_action.moved()

    assert file_action.move is False
    assert file_action.was_moved is True


def test_class_file_action_method_to_hash(file_action):
    assert file_action.hash is False
    assert file_action.was_hashed is False
    
    file_action.to_hash()

    assert file_action.hash is True
    assert file_action.was_hashed is False


def test_class_file_action_method_hashed(file_action):
    assert file_action.hash is False
    assert file_action.was_hashed is False
    
    file_action.hashed()

    assert file_action.hash is False
    assert file_action.was_hashed is True


def test_class_file_action_method_to_list(file_action):
    assert file_action.list is False
    assert file_action.was_listed is False
    
    file_action.to_list()

    assert file_action.list is True
    assert file_action.was_listed is False


def test_class_file_action_method_listed(file_action):
    assert file_action.list is False
    assert file_action.was_listed is False
    
    file_action.listed()

    assert file_action.list is False
    assert file_action.was_listed is True


def test_class_file_action_method_to_preview(file_action):
    assert file_action.preview is False
    assert file_action.was_previewed is False
    
    file_action.to_preview()

    assert file_action.preview is True
    assert file_action.was_previewed is False


def test_class_file_action_method_previewed(file_action):
    assert file_action.preview is False
    assert file_action.was_previewed is False
    
    file_action.previewed()

    assert file_action.preview is False
    assert file_action.was_previewed is True


def test_class_file_action_method_to_thumbnail(file_action):
    assert file_action.thumbnail is False
    assert file_action.was_thumbnailed is False
    
    file_action.to_thumbnail()

    assert file_action.thumbnail is True
    assert file_action.was_thumbnailed is False


def test_class_file_action_method_thumbnailed(file_action):
    assert file_action.thumbnail is False
    assert file_action.was_thumbnailed is False
    
    file_action.thumbnailed()

    assert file_action.thumbnail is False
    assert file_action.was_thumbnailed is True
