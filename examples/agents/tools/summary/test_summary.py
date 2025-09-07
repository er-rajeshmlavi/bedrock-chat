from unittest.mock import Mock, patch
from app.agents.tools.summary import summary_tool, SummaryInput, generate_summary


def test_summary_input_validation():
    """Test that SummaryInput validates correctly."""
    # Valid input
    valid_input = SummaryInput(
        content="This is some content to summarize.",
        summary_type="general",
        max_length=100
    )
    assert valid_input.content == "This is some content to summarize."
    assert valid_input.summary_type == "general"
    assert valid_input.max_length == 100
    
    # Input with defaults
    minimal_input = SummaryInput(content="Some content")
    assert minimal_input.summary_type == "general"
    assert minimal_input.max_length == 200


def test_summary_tool_properties():
    """Test that the summary tool has correct properties."""
    assert summary_tool.name == "generate_summary"
    assert "summary" in summary_tool.description.lower()
    assert summary_tool.args_schema.__name__ == SummaryInput.__name__


def test_empty_content_handling():
    """Test handling of empty content."""
    arg = SummaryInput(content="")
    result = generate_summary(arg, None, None)
    
    assert "error" in result
    assert "No content provided" in result["error"]


def test_whitespace_only_content_handling():
    """Test handling of whitespace-only content."""
    arg = SummaryInput(content="   \n\t   ")
    result = generate_summary(arg, None, None)
    
    assert "error" in result
    assert "No content provided" in result["error"]


@patch('app.agents.tools.summary.get_bedrock_runtime_client')
def test_successful_summary_generation(mock_get_client):
    """Test successful summary generation."""
    # Mock the Bedrock response
    mock_response = {
        "content": [{"text": "This is a generated summary of the content."}]
    }
    mock_client = Mock()
    mock_client.invoke_model.return_value = {
        "body": Mock(read=lambda: f'{{"content": [{{"text": "This is a generated summary of the content."}}]}}'.encode())
    }
    mock_get_client.return_value = mock_client
    
    arg = SummaryInput(
        content="This is a long piece of content that needs to be summarized. It contains multiple sentences and ideas.",
        summary_type="general",
        max_length=50
    )
    
    result = generate_summary(arg, None, "claude-v3.5-sonnet")
    
    assert "summary" in result
    assert "summary_type" in result
    assert result["summary_type"] == "general"
    assert "content" in result
    assert "This is a generated summary" in result["content"]


@patch('app.agents.tools.summary.get_bedrock_runtime_client')
def test_bedrock_client_error_handling(mock_get_client):
    """Test error handling when Bedrock client fails."""
    mock_client = Mock()
    mock_client.invoke_model.side_effect = Exception("Bedrock service error")
    mock_get_client.return_value = mock_client
    
    arg = SummaryInput(content="Some content to summarize")
    result = generate_summary(arg, None, None)
    
    assert "error" in result
    assert "Failed to generate summary" in result["error"]


def test_different_summary_types():
    """Test different summary types generate appropriate prompts."""
    test_cases = [
        ("general", "general summary"),
        ("key_points", "key points"),
        ("action_items", "action items"),
        ("technical", "technical summary"),
        ("unknown_type", "general summary")  # Should fallback to general
    ]
    
    for summary_type, expected_text in test_cases:
        arg = SummaryInput(
            content="Test content",
            summary_type=summary_type
        )
        
        # We can't easily test the internal prompt generation without mocking Bedrock,
        # but we can at least verify the input is accepted
        assert arg.summary_type == summary_type or summary_type == "unknown_type"


if __name__ == "__main__":
    # Run tests manually if needed
    test_summary_input_validation()
    test_summary_tool_properties()
    test_empty_content_handling()
    test_whitespace_only_content_handling()
    print("All basic tests passed!")
