#!/usr/bin/env python3
"""
Test script for chat interface with automatic diagram generation.
"""
import asyncio
import json
import requests

def test_chat_with_diagrams():
    """Test the enhanced chat interface that auto-generates diagrams."""
    
    # Test queries that should trigger diagram generation
    test_queries = [
        "Can you design a microservices architecture for an e-commerce platform?",
        "Show me a system diagram for a social media application",
        "Create a database schema for a user management system",
        "Visualize the architecture of a streaming service",
        "Draw a workflow for processing online orders"
    ]
    
    print("🤖 Testing Enhanced Chat Interface with Auto-Diagram Generation")
    print("=" * 60)
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n📝 Test {i}: {query}")
        print("-" * 50)
        
        try:
            response = requests.post(
                'http://localhost:8000/api/chat',
                json={
                    "message": query,
                    "user_id": f"test_user_{i}",
                    "session_id": f"test_session_{i}"
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Success: {data['success']}")
                print(f"💬 Response: {data['message'][:200]}...")
                
                # Check for artifacts (diagrams)
                if data.get('artifacts') and data['artifacts'].get('diagrams'):
                    diagrams = data['artifacts']['diagrams']
                    print(f"🎨 Generated {len(diagrams)} diagram(s):")
                    
                    for diagram in diagrams:
                        print(f"   - Diagram ID: {diagram['id']}")
                        print(f"   - Artifact ID: {diagram['artifact_id']}")
                        print(f"   - Description: {diagram['description']}")
                        print(f"   - View URL: http://localhost:8000/api/whiteboard/artifacts/{diagram['artifact_id']}")
                        
                        # Test if we can access the PNG
                        png_response = requests.get(f"http://localhost:8000/api/whiteboard/artifacts/{diagram['artifact_id']}")
                        if png_response.status_code == 200:
                            print(f"   - PNG Size: {len(png_response.content)} bytes ✅")
                        else:
                            print(f"   - PNG Access: Failed ({png_response.status_code}) ❌")
                else:
                    print("📋 No diagrams generated (normal for non-diagram queries)")
                    
            else:
                print(f"❌ Error: {response.status_code} - {response.text}")
                
        except Exception as e:
            print(f"❌ Exception: {e}")
        
        print()
    
    print("🏁 Test completed!")
    print("\n💡 Tips for viewing diagrams:")
    print("1. Copy the 'View URL' into your browser to see the PNG")
    print("2. Diagrams are auto-generated when queries contain keywords like:")
    print("   - 'architecture', 'diagram', 'design', 'visualize', 'draw'")
    print("3. The chat response will mention when a diagram is generated")

if __name__ == "__main__":
    test_chat_with_diagrams()
