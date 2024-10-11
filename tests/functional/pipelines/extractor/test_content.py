import pytest

from filejacket.pipelines.extractor.content import MimeTypeFromContentExtractor


@pytest.mark.parametrize(
    "file_fixture, expected_result",
    [("file_7zip", "application/x-7z-compressed")]
)
def test_method_extract_from_MimeTypeFromContentExtractor_with_empty_file_content_mimetype_should_change_it(request, file_fixture, expected_result):
    file_object = request.getfixturevalue(file_fixture)
    
    original_mimetype = file_object.mime_type 
    file_object.mime_type = None
    
    result = MimeTypeFromContentExtractor.extract(file_object=file_object, overrider=False)
    
    assert file_object.mime_type == expected_result
    assert result is None
    
    # Reset original to avoid leak test
    file_object.mime_type = original_mimetype


@pytest.mark.parametrize(
    "file_fixture, fake_mimetype", [
        ("file_7zip", "teste/mimetype")
    ]
)
def test_method_extract_from_MimeTypeFromContentExtractor_with_file_content_mimetype_should_change_with_override(request, file_fixture, fake_mimetype):
    file_object = request.getfixturevalue(file_fixture)
    
    original_mimetype = file_object.mime_type 
    file_object.mime_type = fake_mimetype
    
    result = MimeTypeFromContentExtractor.extract(file_object=file_object, overrider=True)
    
    assert file_object.mime_type != fake_mimetype
    assert result is None
    
    # Reset original to avoid leak test
    file_object.mime_type = original_mimetype
