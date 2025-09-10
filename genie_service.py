"""
Genie Service Module for Databricks AI/BI Integration
Handles conversation management and query processing for inventory data analysis.
"""

import pandas as pd
import os
import time
from databricks import sdk
from typing import Dict, List, Optional, Tuple, Any
import json

class GenieService:
    """Service class for managing Databricks Genie conversations and queries."""
    
    def __init__(self, workspace_client: sdk.WorkspaceClient):
        self.workspace_client = workspace_client
        self.genie_space_id = os.getenv('GENIE_SPACE_ID')
        self.conversations = {}  # Store active conversations
        
    def is_configured(self) -> bool:
        """Check if Genie is properly configured."""
        return self.genie_space_id is not None
    
    def get_query_result(self, statement_id: str) -> Optional[pd.DataFrame]:
        """
        Retrieve query results from Databricks statement execution.
        For simplicity, assumes data fits in one chunk.
        """
        try:
            result = self.workspace_client.statement_execution.get_statement(statement_id)
            
            if not result.result or not result.result.data_array:
                return None
                
            # Convert to DataFrame
            columns = [col.name for col in result.manifest.schema.columns]
            data = result.result.data_array
            
            return pd.DataFrame(data, columns=columns)
            
        except Exception as e:
            print(f"Error retrieving query result: {e}")
            return None
    
    def process_genie_response(self, response) -> Dict[str, Any]:
        """
        Process Genie response and extract text, queries, and data.
        Returns structured response data.
        """
        processed_response = {
            'text_content': [],
            'queries': [],
            'data_frames': [],
            'generated_code': []
        }
        
        try:
            for attachment in response.attachments:
                if attachment.text:
                    processed_response['text_content'].append({
                        'content': attachment.text.content,
                        'type': 'text'
                    })
                elif attachment.query:
                    # Get query description and generated SQL
                    query_info = {
                        'description': attachment.query.description,
                        'generated_sql': attachment.query.query,
                        'statement_id': attachment.query.statement_id,
                        'type': 'query'
                    }
                    processed_response['queries'].append(query_info)
                    
                    # Execute query and get data
                    df = self.get_query_result(attachment.query.statement_id)
                    if df is not None:
                        processed_response['data_frames'].append({
                            'data': df.to_dict('records'),
                            'columns': df.columns.tolist(),
                            'shape': df.shape,
                            'statement_id': attachment.query.statement_id
                        })
                        processed_response['generated_code'].append(attachment.query.query)
            
            return processed_response
            
        except Exception as e:
            print(f"Error processing Genie response: {e}")
            return processed_response
    
    def start_conversation(self, prompt: str) -> Dict[str, Any]:
        """
        Start a new Genie conversation.
        Returns conversation data including ID and initial response.
        """
        if not self.is_configured():
            return {
                'success': False,
                'error': 'Genie not configured. Please set GENIE_SPACE_ID environment variable.'
            }
        
        try:
            # Start conversation
            conversation = self.workspace_client.genie.start_conversation_and_wait(
                self.genie_space_id, 
                prompt
            )
            
            # Process the response
            processed_response = self.process_genie_response(conversation)
            
            # Store conversation
            conversation_data = {
                'conversation_id': conversation.conversation_id,
                'space_id': self.genie_space_id,
                'created_at': time.time(),
                'messages': [{
                    'role': 'user',
                    'content': prompt,
                    'timestamp': time.time()
                }],
                'responses': [processed_response]
            }
            
            self.conversations[conversation.conversation_id] = conversation_data
            
            return {
                'success': True,
                'conversation_id': conversation.conversation_id,
                'response': processed_response,
                'conversation_data': conversation_data
            }
            
        except Exception as e:
            print(f"Error starting Genie conversation: {e}")
            return {
                'success': False,
                'error': f'Failed to start conversation: {str(e)}'
            }
    
    def send_message(self, conversation_id: str, message: str) -> Dict[str, Any]:
        """
        Send a message to an existing Genie conversation.
        Returns updated conversation data.
        """
        if not self.is_configured():
            return {
                'success': False,
                'error': 'Genie not configured. Please set GENIE_SPACE_ID environment variable.'
            }
        
        if conversation_id not in self.conversations:
            return {
                'success': False,
                'error': 'Conversation not found.'
            }
        
        try:
            # Send message to existing conversation
            follow_up_conversation = self.workspace_client.genie.create_message_and_wait(
                self.genie_space_id,
                conversation_id,
                message
            )
            
            # Process the response
            processed_response = self.process_genie_response(follow_up_conversation)
            
            # Update conversation data
            conversation_data = self.conversations[conversation_id]
            conversation_data['messages'].append({
                'role': 'user',
                'content': message,
                'timestamp': time.time()
            })
            conversation_data['responses'].append(processed_response)
            conversation_data['last_updated'] = time.time()
            
            return {
                'success': True,
                'conversation_id': conversation_id,
                'response': processed_response,
                'conversation_data': conversation_data
            }
            
        except Exception as e:
            print(f"Error sending message to Genie: {e}")
            return {
                'success': False,
                'error': f'Failed to send message: {str(e)}'
            }
    
    def get_conversation(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """Get conversation data by ID."""
        return self.conversations.get(conversation_id)
    
    def get_all_conversations(self) -> Dict[str, Dict[str, Any]]:
        """Get all active conversations."""
        return self.conversations
    
    def clear_conversation(self, conversation_id: str) -> bool:
        """Clear a specific conversation from memory."""
        if conversation_id in self.conversations:
            del self.conversations[conversation_id]
            return True
        return False
    
    def clear_all_conversations(self) -> int:
        """Clear all conversations from memory."""
        count = len(self.conversations)
        self.conversations.clear()
        return count
    
    def get_conversation_summary(self, conversation_id: str) -> Dict[str, Any]:
        """Get a summary of conversation activity."""
        conversation = self.get_conversation(conversation_id)
        if not conversation:
            return {'error': 'Conversation not found'}
        
        return {
            'conversation_id': conversation_id,
            'message_count': len(conversation['messages']),
            'response_count': len(conversation['responses']),
            'created_at': conversation['created_at'],
            'last_updated': conversation.get('last_updated', conversation['created_at']),
            'has_queries': any(
                len(response.get('queries', [])) > 0 
                for response in conversation['responses']
            ),
            'has_data': any(
                len(response.get('data_frames', [])) > 0 
                for response in conversation['responses']
            )
        }
    
    def get_suggested_queries(self) -> List[str]:
        """Get suggested queries for inventory analysis."""
        return [
            "What are the top 10 items by inventory value?",
            "Which categories have the most items?",
            "Show me items that are low in stock",
            "What's the total inventory value by category?",
            "Which suppliers provide the most items?",
            "Show me items added in the last 30 days",
            "What are the most expensive items in inventory?",
            "Which locations have the most inventory?",
            "Show me items with quantity below minimum stock level",
            "What's the average price by category?"
        ]
