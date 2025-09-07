# Summary Tool

## Overview

The Summary Tool is a custom tool designed to generate summaries of provided content using Amazon Bedrock models. This tool helps users quickly get concise summaries of conversations, documents, or any text content, with different summary types for various use cases.

## Features

- **Multiple Summary Types**:
  - `general`: Overall summary of the content
  - `key_points`: Extract and list main points
  - `action_items`: Identify tasks and next steps
  - `technical`: Technical summary highlighting important details

- **Configurable Length**: Set maximum length for summaries (default: 200 words)

- **Model Support**: Uses Amazon Bedrock models, with fallback to Claude 3.5 Sonnet

## How to enable this tool

1. The tool is already implemented in `backend/app/agents/tools/summary.py`
2. It's already registered in `backend/app/agents/utils.py`
3. Deploy the changes:
   ```bash
   npx cdk deploy
   ```

## Usage Examples

Users can ask the chatbot to summarize content in natural language:

### Basic Summary
- "Can you summarize this conversation?"
- "Please provide a summary of the discussion"
- "Summarize the key points from our chat"

### Specific Summary Types
- "Give me the action items from this discussion"
- "What are the key points from this conversation?"
- "Provide a technical summary of the implementation details"

### With Custom Length
- "Give me a brief 100-word summary"
- "Provide a detailed 300-word summary"

## Tool Parameters

The tool accepts the following parameters:

- `content` (required): The text content to summarize
- `summary_type` (optional): Type of summary - "general", "key_points", "action_items", or "technical"
- `max_length` (optional): Maximum length in words (default: 200)

## Example Tool Usage

When a user asks for a summary, the chatbot will automatically invoke this tool with appropriate parameters:

```json
{
  "content": "Long conversation or document text here...",
  "summary_type": "general",
  "max_length": 200
}
```

## Response Format

The tool returns a structured response with:

- `summary`: The generated summary text
- `summary_type`: Type of summary that was generated
- `original_length`: Word count of original content
- `summary_length`: Word count of the summary
- `content`: Formatted summary for display
- `source_name`: Tool identifier

## Error Handling

The tool handles various error cases:

- Empty or whitespace-only content
- Bedrock service errors
- Model response parsing errors
- Invalid parameters

## Testing

Run the test suite:

```bash
python backend/app/agents/tools/test_summary.py
```

## Dependencies

- Amazon Bedrock Runtime client
- Pydantic for input validation
- Standard logging for error tracking

## Integration with Chat Interface

Once deployed, users can simply ask for summaries in natural language, and the chatbot will automatically use this tool to provide structured, helpful summaries of their content.
