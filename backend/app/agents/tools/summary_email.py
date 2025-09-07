from app.agents.tools.agent_tool import AgentTool
from app.repositories.models.custom_bot import BotModel
from app.routes.schemas.conversation import type_model_name
from app.bedrock import get_model_id
from app.utils import get_bedrock_runtime_client
from pydantic import BaseModel, Field
from typing import Optional
import json
import logging
import re
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

logger = logging.getLogger(__name__)


def send_summary_email(
    recipient_email: str,
    summary_content: str,
    summary_type: str = "general",
    sender_email: str = "mrmalviyalalit@gmail.com",
    sender_password: str = "bktrzqcdhlifcssj"
) -> dict:
    """
    Send a summary email using Gmail SMTP
    """
    try:
        # Create message
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = recipient_email
        
        # Create subject with timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        msg['Subject'] = f"Chat Summary - {summary_type.title()} ({timestamp})"
        
        # Create email body
        body = create_email_body(summary_content, summary_type, timestamp)
        msg.attach(MIMEText(body, 'html'))
        
        # Send email
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender_email, sender_password)
        
        text = msg.as_string()
        server.sendmail(sender_email, recipient_email, text)
        server.quit()
        
        logger.info(f"Summary email sent successfully to {recipient_email}")
        
        return {
            "success": True,
            "message": f"Summary email sent successfully to {recipient_email}",
            "sent_at": timestamp,
            "subject": msg['Subject']
        }
        
    except Exception as e:
        error_msg = f"Failed to send email: {str(e)}"
        logger.error(error_msg)
        return {
            "success": False,
            "error": error_msg
        }


def create_email_body(summary_content: str, summary_type: str, timestamp: str) -> str:
    """Create formatted HTML email body"""
    
    # Define icons and colors for different summary types
    type_info = {
        "general": {"icon": "📄", "color": "#2563eb"},
        "key_points": {"icon": "🔑", "color": "#dc2626"},
        "action_items": {"icon": "✅", "color": "#16a34a"},
        "technical": {"icon": "⚙️", "color": "#9333ea"}
    }
    
    info = type_info.get(summary_type, type_info["general"])
    
    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Chat Summary</title>
        <style>
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                line-height: 1.6;
                margin: 0;
                padding: 0;
                background-color: #f5f5f5;
            }}
            .container {{
                max-width: 600px;
                margin: 0 auto;
                background-color: white;
                border-radius: 8px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                overflow: hidden;
            }}
            .header {{
                background-color: {info['color']};
                color: white;
                padding: 20px;
                text-align: center;
            }}
            .header h1 {{
                margin: 0;
                font-size: 24px;
            }}
            .content {{
                padding: 30px;
            }}
            .summary-type {{
                background-color: #f8f9fa;
                border-left: 4px solid {info['color']};
                padding: 15px;
                margin: 20px 0;
                border-radius: 4px;
            }}
            .summary-text {{
                white-space: pre-wrap;
                font-size: 16px;
                line-height: 1.8;
                color: #333;
            }}
            .footer {{
                background-color: #f8f9fa;
                padding: 20px;
                text-align: center;
                font-size: 14px;
                color: #666;
                border-top: 1px solid #e9ecef;
            }}
            .timestamp {{
                color: #6c757d;
                font-size: 14px;
                margin-top: 20px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>{info['icon']} Chat Summary</h1>
            </div>
            
            <div class="content">
                <div class="summary-type">
                    <strong>{info['icon']} {summary_type.replace('_', ' ').title()} Summary</strong>
                </div>
                
                <div class="summary-text">
{summary_content}
                </div>
                
                <div class="timestamp">
                    <strong>Generated:</strong> {timestamp}
                </div>
            </div>
            
            <div class="footer">
                <p>This summary was automatically generated by your AI assistant.</p>
                │          Powered by Selira Chat Summary Tool              │
            </div>
        </div>
    </body>
    </html>
    """
    
    return html_body


class SummaryEmailInput(BaseModel):
    content: str = Field(description="The content to summarize. This can be conversation history, text, or any content that needs to be summarized.")
    summary_type: Optional[str] = Field(
        default="general",
        description="Type of summary requested: 'general' for overall summary, 'key_points' for main points, 'action_items' for actionable items, or 'technical' for technical summary."
    )
    max_length: Optional[int] = Field(
        default=200,
        description="Maximum length of the summary in words (default: 200)"
    )
    send_email: Optional[bool] = Field(
        default=False,
        description="Whether to send the summary via email (default: False)"
    )
    recipient_email: Optional[str] = Field(
        default=None,
        description="Email address to send the summary to (required if send_email is True). Example: user@example.com"
    )


def generate_summary_with_email(
    arg: SummaryEmailInput, bot: BotModel | None, model: type_model_name | None
) -> dict:
    """
    Generate a summary of the provided content using Amazon Bedrock and optionally send via email.
    """
    try:
        content = arg.content
        summary_type = arg.summary_type or "general"
        max_length = arg.max_length or 200
        send_email = arg.send_email or False
        recipient_email = arg.recipient_email
        
        if not content.strip():
            return {
                "error": "No content provided to summarize",
                "content": "Please provide content that needs to be summarized."
            }
        
        # Validate email if email sending is requested
        if send_email:
            if not recipient_email:
                # Try to extract email from content if not provided
                email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
                found_emails = re.findall(email_pattern, content)
                if found_emails:
                    recipient_email = found_emails[0]
                else:
                    return {
                        "error": "Email address required when send_email is True",
                        "content": "Please provide a recipient email address to send the summary."
                    }
            
            # Validate email format
            email_pattern = r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}$'
            if not re.match(email_pattern, recipient_email):
                return {
                    "error": f"Invalid email format: {recipient_email}",
                    "content": "Please provide a valid email address."
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
        
        # Prepare the base result
        result = {
            "summary": summary_text.strip(),
            "summary_type": summary_type,
            "original_length": len(content.split()),
            "summary_length": len(summary_text.split()),
            "content": f"Summary ({summary_type}): {summary_text.strip()}",
            "source_name": "Summary Tool",
        }
        
        # Send email if requested
        if send_email and recipient_email:
            try:
                email_result = send_summary_email(
                    recipient_email=recipient_email,
                    summary_content=summary_text.strip(),
                    summary_type=summary_type
                )
                
                if email_result["success"]:
                    result["email_sent"] = True
                    result["email_recipient"] = recipient_email
                    result["email_sent_at"] = email_result["sent_at"]
                    result["content"] += f"\n\n📧 Summary email sent successfully to {recipient_email}"
                else:
                    result["email_sent"] = False
                    result["email_error"] = email_result["error"]
                    result["content"] += f"\n\n❌ Failed to send email: {email_result['error']}"
                    
            except Exception as e:
                result["email_sent"] = False
                result["email_error"] = str(e)
                result["content"] += f"\n\n❌ Email sending failed: {str(e)}"
        
        return result
        
    except Exception as e:
        logger.error(f"Error generating summary: {str(e)}")
        return {
            "error": f"Failed to generate summary: {str(e)}",
            "content": "An error occurred while generating the summary. Please try again."
        }


summary_email_tool = AgentTool(
    name="generate_summary_with_email",
    description="Generate a summary of provided content and optionally send it via email. Can create general summaries, extract key points, identify action items, or provide technical summaries. Supports email delivery to specified recipients. Useful when users ask to summarize conversations and send them via email.",
    args_schema=SummaryEmailInput,
    function=generate_summary_with_email,
)
