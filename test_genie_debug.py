#!/usr/bin/env python3
"""
Debug script for Genie integration to test the API and response structure.
"""

import os
import sys
from databricks import sdk

def test_genie_api():
    """Test Genie API directly to understand the response structure."""
    try:
        # Initialize workspace client
        workspace_client = sdk.WorkspaceClient()
        print("✅ Databricks SDK connection successful")
        
        # Get Genie space ID
        genie_space_id = os.getenv('GENIE_SPACE_ID')
        if not genie_space_id:
            print("❌ GENIE_SPACE_ID environment variable not set")
            return False
        
        print(f"✅ Genie Space ID: {genie_space_id}")
        
        # Test a simple conversation
        test_prompt = "What tables are available in the inventory database?"
        print(f"🧪 Testing with prompt: {test_prompt}")
        
        try:
            # Start conversation
            conversation = workspace_client.genie.start_conversation_and_wait(
                genie_space_id, 
                test_prompt
            )
            
            print(f"✅ Conversation started successfully")
            print(f"   Conversation ID: {conversation.conversation_id}")
            print(f"   Response type: {type(conversation)}")
            
            # Inspect the response structure
            print(f"\n📋 Response attributes:")
            for attr in dir(conversation):
                if not attr.startswith('_'):
                    try:
                        value = getattr(conversation, attr)
                        if callable(value):
                            print(f"   {attr}: <method>")
                        else:
                            print(f"   {attr}: {type(value)} = {value}")
                    except Exception as e:
                        print(f"   {attr}: <error accessing: {e}>")
            
            # Check attachments
            if hasattr(conversation, 'attachments'):
                print(f"\n📎 Attachments ({len(conversation.attachments)}):")
                for i, attachment in enumerate(conversation.attachments):
                    print(f"   Attachment {i}:")
                    print(f"     Type: {type(attachment)}")
                    for attr in dir(attachment):
                        if not attr.startswith('_'):
                            try:
                                value = getattr(attachment, attr)
                                if callable(value):
                                    print(f"     {attr}: <method>")
                                else:
                                    print(f"     {attr}: {type(value)} = {value}")
                            except Exception as e:
                                print(f"     {attr}: <error accessing: {e}>")
                    
                    # Check if it's a query attachment
                    if hasattr(attachment, 'query') and attachment.query:
                        print(f"     Query object attributes:")
                        for attr in dir(attachment.query):
                            if not attr.startswith('_'):
                                try:
                                    value = getattr(attachment.query, attr)
                                    if callable(value):
                                        print(f"       {attr}: <method>")
                                    else:
                                        print(f"       {attr}: {type(value)} = {value}")
                                except Exception as e:
                                    print(f"       {attr}: <error accessing: {e}>")
            
            return True
            
        except Exception as e:
            print(f"❌ Error testing Genie conversation: {e}")
            import traceback
            traceback.print_exc()
            return False
            
    except Exception as e:
        print(f"❌ Error initializing Databricks client: {e}")
        return False

def main():
    """Run Genie API debug test."""
    print("🧪 Genie API Debug Test")
    print("=" * 50)
    
    success = test_genie_api()
    
    print("\n" + "=" * 50)
    if success:
        print("✅ Genie API test completed successfully")
        print("📝 Check the output above to understand the response structure")
    else:
        print("❌ Genie API test failed")
        print("🔧 Make sure GENIE_SPACE_ID is set and you have proper permissions")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
