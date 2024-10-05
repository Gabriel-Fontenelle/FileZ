import pytest

from filejacket.exception import (
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
    assert isinstance(exception_class, Exception)
