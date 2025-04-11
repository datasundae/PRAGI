#!/usr/bin/env python3
"""Test script for conversation logging functionality."""

import os
import sys
from datetime import datetime
from pathlib import Path

# Add the project root to the Python path
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent.parent
sys.path.append(str(project_root))

from src.logger.conversation_logger import ConversationLogger

def test_logging():
    """Test the conversation logging functionality."""
    # Initialize logger with a test directory
    test_log_dir = "logs/test_conversations"
    logger = ConversationLogger(log_dir=test_log_dir)
    
    print(f"\n🔍 Testing conversation logger...")
    print(f"Logs will be saved to: {test_log_dir}")
    
    # Simulate a conversation
    conversation = [
        {
            "role": "user",
            "content": "How do I use the vector database search?",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        },
        {
            "role": "assistant",
            "content": """The vector database search can be used by:
1. First, ensure your text is ingested
2. Then use the search functionality with a query
3. The results will be returned based on semantic similarity""",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        },
        {
            "role": "user",
            "content": "Can you show me an example?",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        },
        {
            "role": "assistant",
            "content": """Here's an example:
```python
results = vector_db.search(
    query="What is classical philosophy?",
    k=5  # Return top 5 results
)
```""",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    ]
    
    # Test saving entire conversation
    print("\n📝 Testing: Saving entire conversation...")
    success = logger.save_conversation_to_markdown(conversation)
    if success:
        print("✅ Successfully saved conversation")
    else:
        print("❌ Failed to save conversation")
    
    # Test appending individual messages
    print("\n📝 Testing: Appending individual messages...")
    new_messages = [
        {
            "role": "user",
            "content": "That's very helpful, thank you!",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        },
        {
            "role": "assistant",
            "content": "You're welcome! Let me know if you have any other questions.",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    ]
    
    for message in new_messages:
        success = logger.append_to_daily_log(message)
        if success:
            print(f"✅ Successfully appended {message['role']} message")
        else:
            print(f"❌ Failed to append {message['role']} message")
    
    # Test loading the conversation
    print("\n📖 Testing: Loading conversation...")
    content = logger.load_daily_log()
    if content:
        print("✅ Successfully loaded conversation")
        print("\nGenerated Markdown content:")
        print("=" * 50)
        print(content)
        print("=" * 50)
    else:
        print("❌ Failed to load conversation")

def cleanup():
    """Clean up test files."""
    test_log_dir = "logs/test_conversations"
    if os.path.exists(test_log_dir):
        for file in os.listdir(test_log_dir):
            file_path = os.path.join(test_log_dir, file)
            try:
                os.unlink(file_path)
            except Exception as e:
                print(f"Warning: Could not delete {file_path}: {e}")
        try:
            os.rmdir(test_log_dir)
        except Exception as e:
            print(f"Warning: Could not delete {test_log_dir}: {e}")

if __name__ == "__main__":
    try:
        test_logging()
        
        # Ask if user wants to keep the test logs
        response = input("\nWould you like to keep the test logs? (y/n): ").lower()
        if response != 'y':
            cleanup()
            print("🧹 Test logs cleaned up")
        else:
            print("📁 Test logs have been preserved")
            
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        cleanup()
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        cleanup()
        sys.exit(1) 