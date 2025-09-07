from app.agents.tools.agent_tool import AgentTool
from app.repositories.models.custom_bot import BotModel
from app.routes.schemas.conversation import type_model_name
from app.bedrock import get_model_id
from app.utils import get_bedrock_runtime_client
from pydantic import BaseModel, Field
from typing import Optional
import json
import logging

logger = logging.getLogger(__name__)


class SummaryInput(BaseModel):
    content: str = Field(description="The content to summarize. This can be conversation history, text, or any content that needs to be summarized.")
    summary_type: Optional[str] = Field(
        default="general",
        description="Type of summary requested: 'general' for overall summary, 'key_points' for main points, 'action_items' for actionable items, or 'technical' for technical summary."
    )
    max_length: Optional[int] = Field(
        default=200,
        description="Maximum length of the summary in words (default: 200)"
    )


def generate_summary(
    arg: SummaryInput, bot: BotModel | None, model: type_model_name | None
) -> dict:
    """
    Generate a summary of the provided content using Amazon Bedrock.
    """
    try:
        content = arg.content
        summary_type = arg.summary_type or "general"
        max_length = arg.max_length or 200
        
        if not content.strip():
            return {
                "error": "No content provided to summarize",
                "content": "Please provide content that needs to be summarized."
            }
        
        # Create the prompt based on summary type
        prompts = {
            "general": f"Please provide a concise general summary of the following content in approximately {max_length} words:",
            "key_points": f"Please extract and list the key points from the following content in approximately {max_length} words:",
            "action_items": f"Please identify and list any action items, tasks, or next steps from the following content in approximately {max_length} words:",
            "technical": f"Please provide a technical summary highlighting important technical details from the following content in approximately {max_length} words:"
        }
        
        prompt = prompts.get(summary_type, prompts["general"])
        full_prompt = f"{prompt}\n\nContent to summarize:\n{content}\n\nSummary:"
        
        # Initialize Bedrock client
        bedrock_runtime = get_bedrock_runtime_client()
        
        # Use Claude model for summarization (fallback to default if model not specified)
        model_id = get_model_id(model) if model else get_model_id("claude-v3.5-sonnet")
        
        # Prepare the request body based on the model
        if "anthropic.claude" in model_id:
            body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": max_length * 2,  # Allow some buffer for the response
                "messages": [
                    {
                        "role": "user",
                        "content": full_prompt
                    }
                ],
                "temperature": 0.3  # Lower temperature for more focused summaries
            }
        else:
            # Fallback for other models
            body = {
                "inputText": full_prompt,
                "textGenerationConfig": {
                    "maxTokenCount": max_length * 2,
                    "temperature": 0.3
                }
            }
        
        # Invoke the model
        response = bedrock_runtime.invoke_model(
            body=json.dumps(body),
            modelId=model_id,
            accept="application/json",
            contentType="application/json"
        )
        
        # Parse the response
        response_body = json.loads(response.get("body").read())
        
        if "anthropic.claude" in model_id:
            summary_text = response_body["content"][0]["text"]
        else:
            # Handle other model response formats
            summary_text = response_body.get("results", [{}])[0].get("outputText", "")
        
        if not summary_text.strip():
            return {
                "error": "Failed to generate summary",
                "content": "The model did not return a valid summary."
            }
        
        return {
            "summary": summary_text.strip(),
            "summary_type": summary_type,
            "original_length": len(content.split()),
            "summary_length": len(summary_text.split()),
            "content": f"Summary ({summary_type}): {summary_text.strip()}",
            "source_name": "Summary Tool",
        }
        
    except Exception as e:
        logger.error(f"Error generating summary: {str(e)}")
        return {
            "error": f"Failed to generate summary: {str(e)}",
            "content": "An error occurred while generating the summary. Please try again."
        }


summary_tool = AgentTool(
    name="generate_summary",
    description="Generate a summary of provided content. Can create general summaries, extract key points, identify action items, or provide technical summaries. Useful when users ask to summarize conversations, documents, or any text content.",
    args_schema=SummaryInput,
    function=generate_summary,
)
