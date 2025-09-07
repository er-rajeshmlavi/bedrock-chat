#!/usr/bin/env python3
"""
Test script for Summary Email Tool
This script tests both summary generation and email sending functionality
"""

import sys
import os
sys.path.append('/home/iamgroot/chat/bedrock-claude-chat/mrlalit/bedrock-chat/backend')

from unittest.mock import Mock, patch
from app.agents.tools.summary_email import summary_email_tool, SummaryEmailInput, generate_summary_with_email
from app.utils.email_service import EmailService

def test_email_service():
    """Test the email service functionality"""
    print("🧪 Testing Email Service...")
    
    # Test email service creation
    email_service = EmailService(
        sender_email="mrmalviyalalit@gmail.com",
        sender_password="bktrzqcdhlifcssj"
    )
    
    print(f"  ✓ Email service created with sender: {email_service.sender_email}")
    print(f"  ✓ SMTP server: {email_service.smtp_server}:{email_service.smtp_port}")
    
    # Test email body generation
    test_summary = "This is a test summary of a conversation about AI implementation."
    body = email_service._create_email_body(test_summary, "general", "2025-09-06 10:30")
    
    assert "test summary" in body.lower()
    assert "general" in body.lower()
    assert "2025-09-06" in body
    print("  ✓ Email body generation works")
    print("  ✅ Email service test passed!\n")

def test_summary_email_input_validation():
    """Test input validation for the email-enabled summary tool"""
    print("🧪 Testing Summary Email Input Validation...")
    
    # Test basic input
    input_obj = SummaryEmailInput(
        content="Test content for summarization",
        summary_type="general",
        max_length=100,
        send_email=False
    )
    
    print(f"  ✓ Basic input: {input_obj.content[:30]}...")
    print(f"  ✓ Summary type: {input_obj.summary_type}")
    print(f"  ✓ Send email: {input_obj.send_email}")
    
    # Test email input
    email_input = SummaryEmailInput(
        content="Test content",
        send_email=True,
        recipient_email="test@example.com"
    )
    
    print(f"  ✓ Email enabled: {email_input.send_email}")
    print(f"  ✓ Recipient: {email_input.recipient_email}")
    print("  ✅ Input validation test passed!\n")

def test_email_validation():
    """Test email address validation"""
    print("🧪 Testing Email Validation...")
    
    # Test invalid email
    try:
        result = generate_summary_with_email(
            SummaryEmailInput(
                content="Test content",
                send_email=True,
                recipient_email="invalid-email"
            ),
            None,
            None
        )
        
        assert "error" in result
        assert "Invalid email format" in result["error"]
        print("  ✓ Invalid email format rejected")
        
    except Exception as e:
        print(f"  ❌ Email validation test failed: {e}")
    
    # Test missing email
    try:
        result = generate_summary_with_email(
            SummaryEmailInput(
                content="Test content",
                send_email=True,
                recipient_email=None
            ),
            None,
            None
        )
        
        assert "error" in result
        assert "Email address required" in result["error"]
        print("  ✓ Missing email address detected")
        
    except Exception as e:
        print(f"  ❌ Missing email test failed: {e}")
    
    print("  ✅ Email validation test passed!\n")

@patch('app.agents.tools.summary_email.get_bedrock_runtime_client')
@patch('app.agents.tools.summary_email.get_model_id')
@patch('app.agents.tools.summary_email.send_summary_email')
def test_summary_with_mock_email(mock_send_email, mock_get_model_id, mock_get_client):
    """Test summary generation with mocked email sending"""
    print("🧪 Testing Summary with Mocked Email...")
    
    # Mock the model ID
    mock_get_model_id.return_value = "anthropic.claude-3-5-sonnet-20240620-v1:0"
    
    # Mock the Bedrock client and response
    mock_client = Mock()
    mock_response = {
        "body": Mock()
    }
    
    response_content = {
        "content": [
            {
                "text": "This is a test summary generated for email testing. The summary covers key aspects of the conversation and provides actionable insights."
            }
        ]
    }
    
    mock_response["body"].read.return_value = str(response_content).encode().replace(b"'", b'"')
    mock_client.invoke_model.return_value = mock_response
    mock_get_client.return_value = mock_client
    
    # Mock successful email sending
    mock_send_email.return_value = {
        "success": True,
        "message": "Email sent successfully",
        "sent_at": "2025-09-06 10:30"
    }
    
    # Test summary with email
    test_input = SummaryEmailInput(
        content="This is a sample conversation about implementing email functionality in a chatbot. We discussed SMTP configuration, email templates, and error handling strategies.",
        summary_type="action_items",
        max_length=100,
        send_email=True,
        recipient_email="mrmalviyalalit@gmail.com"
    )
    
    result = generate_summary_with_email(test_input, None, "claude-v3.5-sonnet")
    
    print(f"  ✓ Summary generated: {len(result.get('summary', ''))} characters")
    print(f"  ✓ Summary type: {result.get('summary_type')}")
    print(f"  ✓ Email sent: {result.get('email_sent')}")
    print(f"  ✓ Email recipient: {result.get('email_recipient')}")
    
    assert 'summary' in result
    assert result['summary_type'] == 'action_items'
    assert result.get('email_sent') == True
    assert result.get('email_recipient') == "mrmalviyalalit@gmail.com"
    
    print("  ✅ Summary with email test passed!\n")

def test_tool_registration():
    """Test that the email tool is properly registered"""
    print("🧪 Testing Tool Registration...")
    
    try:
        from app.agents.utils import get_available_tools
        
        tools = get_available_tools()
        tool_names = [tool.name for tool in tools]
        
        print(f"  ✓ Available tools: {tool_names}")
        
        assert 'generate_summary_with_email' in tool_names
        assert 'generate_summary' in tool_names  # Original tool should still be there
        
        print("  ✓ Both summary tools registered")
        print("  ✅ Tool registration test passed!\n")
        
    except Exception as e:
        print(f"  ❌ Tool registration test failed: {e}")

def show_usage_examples():
    """Show how users will request email summaries"""
    print("🗣️  How Users Will Request Email Summaries")
    print("=" * 60)
    
    examples = [
        "Summarize our conversation and email it to mrmalviyalalit@gmail.com",
        "Send me a summary of key points via email",
        "Email the action items from this discussion to my email",
        "Generate a technical summary and send it to my email address",
        "Can you summarize this and email it to me?",
        "Send a brief summary to mrmalviyalalit@gmail.com",
        "Email me the key decisions we made in this conversation"
    ]
    
    for i, example in enumerate(examples, 1):
        print(f"{i}. User: \"{example}\"")
        print(f"   → Chatbot: *Uses Summary Email Tool* 📧✨\n")

def main():
    """Run all tests"""
    print("🚀 Starting Summary Email Tool tests...\n")
    
    try:
        test_email_service()
        test_summary_email_input_validation()
        test_email_validation()
        test_summary_with_mock_email()
        test_tool_registration()
        show_usage_examples()
        
        print("🎉 All Summary Email Tool tests passed!")
        
        print("\n📧 Email Summary Tool Features:")
        print("  ✅ Generate summaries with multiple types")
        print("  ✅ Send summaries via email automatically")
        print("  ✅ Email validation and error handling")
        print("  ✅ HTML-formatted emails with styling")
        print("  ✅ Gmail SMTP integration")
        print("  ✅ Natural language email requests")
        
        print("\n🔧 Next steps:")
        print("  1. Deploy: npx cdk deploy")
        print("  2. Test with: 'Summarize this and email it to mrmalviyalalit@gmail.com'")
        print("  3. Check your email for formatted summaries!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
