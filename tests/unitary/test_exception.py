import pytest

from filejacket.exception import (
    __all__,
    EmptyContentError,
    ImproperlyConfiguredFile,
    NoInternalContentError,
    ImproperlyConfiguredPipeline,
    OperationNotAllowed,
    PipelineError,
    RenderError,
    ReservedFilenameError,
    SerializerError,
    ValidationError
)


@pytest.mark.parametrize(
    "exception_class",
    [
        EmptyContentError,
        ImproperlyConfiguredFile,
        NoInternalContentError,
        ImproperlyConfiguredPipeline,
        OperationNotAllowed,
        PipelineError,
        RenderError,
        ReservedFilenameError,
        SerializerError,
        ValidationError
    ]
)
def test_instance_of_exception(exception_class):
    assert isinstance(exception_class(), Exception)


def test_file_exception_all_import():
    assert __all__ == [
        'CacheContentNotSeekableError',
        'EmptyContentError',
        'ImproperlyConfiguredFile',
        'ImproperlyConfiguredPipeline',
        'NoInternalContentError',
        'OperationNotAllowed',
        'PipelineError',
        'ValidationError',
        'ReservedFilenameError',
        'RenderError',
        'SerializerError'
    ]
