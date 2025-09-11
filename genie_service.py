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
        # Try to get from config first, then fall back to environment variable
        try:
            from config import config
            self.genie_space_id = config.get_genie_space_id()
        except ImportError:
            self.genie_space_id = os.getenv('GENIE_SPACE_ID')
        self.conversations = {}  # Store active conversations
        
    def is_configured(self) -> bool:
        """Check if Genie is properly configured."""
        return self.genie_space_id is not None
    
    def get_query_result(self, statement_id: str) -> Optional[pd.DataFrame]:
        """
        Retrieve query results from Databricks statement execution.
        Based on Databricks Apps Cookbook implementation.
        For simplicity, assumes data fits in one chunk.
        """
        try:
            result = self.workspace_client.statement_execution.get_statement(statement_id)
            
            # Following the exact pattern from Databricks Apps Cookbook
            if not result.result or not result.result.data_array:
                return None
                
            # Convert to DataFrame exactly as shown in the cookbook
            return pd.DataFrame(
                result.result.data_array, 
                columns=[i.name for i in result.manifest.schema.columns]
            )
            
        except Exception as e:
            print(f"Error retrieving query result: {e}")
            return None
    
    def execute_sql_directly(self, sql_query: str) -> Optional[pd.DataFrame]:
        """
        Execute SQL query directly against the PostgreSQL database.
        This is used when Genie doesn't provide a statement_id.
        """
        try:
            # Import database connection components
            import psycopg
            from psycopg import sql
            import os
            import time
            
            # Get database connection details
            postgres_password = None
            last_password_refresh = 0
            
            def refresh_oauth_token():
                nonlocal postgres_password, last_password_refresh
                if postgres_password is None or time.time() - last_password_refresh > 900:
                    print("Refreshing PostgreSQL OAuth token for direct SQL execution")
                    try:
                        # Use the same method as in the main app
                        postgres_password = self.workspace_client.config.oauth_token().access_token
                        last_password_refresh = time.time()
                    except Exception as e:
                        print(f"❌ Failed to refresh OAuth token: {str(e)}")
                        return False
                return True
            
            # Refresh token and get connection
            if not refresh_oauth_token():
                return None
                
            conn_string = (
                f"dbname={os.getenv('PGDATABASE')} "
                f"user={os.getenv('PGUSER')} "
                f"password={postgres_password} "
                f"host={os.getenv('PGHOST')} "
                f"port={os.getenv('PGPORT')} "
                f"sslmode={os.getenv('PGSSLMODE', 'require')} "
                f"application_name={os.getenv('PGAPPNAME', 'genie_direct_execution')}"
            )
            
            with psycopg.connect(conn_string) as conn:
                with conn.cursor() as cur:
                    # Execute the SQL query
                    cur.execute(sql_query)
                    
                    # Get column names
                    columns = [desc[0] for desc in cur.description] if cur.description else []
                    
                    # Fetch all results
                    rows = cur.fetchall()
                    
                    if not rows:
                        return None
                    
                    # Convert to DataFrame
                    return pd.DataFrame(rows, columns=columns)
                    
        except Exception as e:
            print(f"Error executing SQL directly: {e}")
            return None
    
    def process_genie_response(self, response) -> Dict[str, Any]:
        """
        Process Genie response and extract text, queries, and data.
        Based on Databricks Apps Cookbook implementation.
        Returns structured response data.
        """
        processed_response = {
            'text_content': [],
            'queries': [],
            'data_frames': [],
            'generated_code': []
        }
        
        try:
            # Process attachments exactly as shown in Databricks Apps Cookbook
            for i in response.attachments:
                if i.text:
                    # Handle text response
                    processed_response['text_content'].append({
                        'content': i.text.content,
                        'type': 'text'
                    })
                elif i.query:
                    # Handle query response - with proper debugging
                    print(f"Processing query attachment...")
                    print(f"Query object attributes: {[attr for attr in dir(i.query) if not attr.startswith('_')]}")
                    
                    # Get query details safely
                    query_info = {
                        'description': getattr(i.query, 'description', 'No description available'),
                        'generated_sql': getattr(i.query, 'query', 'No query available'),
                        'type': 'query'
                    }
                    
                    # Try to get statement_id safely
                    statement_id = None
                    if hasattr(i.query, 'statement_id'):
                        statement_id = i.query.statement_id
                        print(f"Found statement_id: {statement_id}")
                    else:
                        print(f"No statement_id found. Available attributes: {[attr for attr in dir(i.query) if not attr.startswith('_')]}")
                        # Try alternative names
                        for attr_name in ['id', 'statementId', 'query_id', 'execution_id']:
                            if hasattr(i.query, attr_name):
                                statement_id = getattr(i.query, attr_name)
                                print(f"Found alternative statement_id as '{attr_name}': {statement_id}")
                                break
                    
                    if statement_id and statement_id != 'None':
                        query_info['statement_id'] = statement_id
                        print(f"Executing query with statement_id: {statement_id}")
                        
                        # Execute query and get data
                        try:
                            data = self.get_query_result(statement_id)
                            if data is not None:
                                print(f"Query executed successfully, got {len(data)} rows")
                                processed_response['data_frames'].append({
                                    'data': data.to_dict('records'),
                                    'columns': data.columns.tolist(),
                                    'shape': data.shape,
                                    'statement_id': statement_id
                                })
                                processed_response['generated_code'].append(query_info['generated_sql'])
                            else:
                                print(f"Query execution returned no data")
                        except Exception as e:
                            print(f"Error executing query: {e}")
                    else:
                        print(f"No valid statement_id available, executing SQL directly against database")
                        # Execute the generated SQL directly against PostgreSQL
                        try:
                            data = self.execute_sql_directly(query_info['generated_sql'])
                            if data is not None:
                                print(f"Direct SQL execution successful, got {len(data)} rows")
                                processed_response['data_frames'].append({
                                    'data': data.to_dict('records'),
                                    'columns': data.columns.tolist(),
                                    'shape': data.shape,
                                    'statement_id': 'direct_execution'
                                })
                                processed_response['generated_code'].append(query_info['generated_sql'])
                            else:
                                print(f"Direct SQL execution returned no data")
                        except Exception as e:
                            print(f"Error executing SQL directly: {e}")
                    
                    processed_response['queries'].append(query_info)
            
            return processed_response
            
        except Exception as e:
            print(f"Error processing Genie response: {e}")
            import traceback
            traceback.print_exc()
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
            print(f"Starting Genie conversation with prompt: {prompt}")
            print(f"Using Genie space ID: {self.genie_space_id}")
            
            # Start conversation
            conversation = self.workspace_client.genie.start_conversation_and_wait(
                self.genie_space_id, 
                prompt
            )
            
            print(f"Conversation started with ID: {conversation.conversation_id}")
            print(f"Response attachments: {len(conversation.attachments) if hasattr(conversation, 'attachments') else 'No attachments'}")
            
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
            import traceback
            traceback.print_exc()
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
            print(f"Sending message to conversation {conversation_id}: {message}")
            
            # Send message to existing conversation
            follow_up_conversation = self.workspace_client.genie.create_message_and_wait(
                self.genie_space_id,
                conversation_id,
                message
            )
            
            print(f"Message sent successfully. Response attachments: {len(follow_up_conversation.attachments) if hasattr(follow_up_conversation, 'attachments') else 'No attachments'}")
            
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
            import traceback
            traceback.print_exc()
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
