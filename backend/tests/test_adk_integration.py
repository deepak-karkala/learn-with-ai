#!/usr/bin/env python3
"""
Integration tests for Google ADK basic functionality.
This verifies Issue #3: Google ADK Basic Setup and Authentication

Unlike test_adk_service.py which tests the service logic with mocks,
this file tests actual Google ADK integration with real API calls.
"""

import os
import sys
from pathlib import Path

import pytest
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add app directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "app"))


class TestADKIntegration:
    """Integration tests for Google ADK - tests real API calls"""

    def test_environment_setup(self):
        """Test environment variables are properly configured"""
        api_key = os.getenv("GOOGLE_API_KEY")
        use_vertex = os.getenv("GOOGLE_GENAI_USE_VERTEXAI", "FALSE").upper() == "TRUE"
        
        # We need either API key or Vertex AI setup
        assert api_key or use_vertex, "Either GOOGLE_API_KEY or Vertex AI must be configured"
        
        if use_vertex:
            assert os.getenv("GOOGLE_CLOUD_PROJECT"), "GOOGLE_CLOUD_PROJECT required for Vertex AI"

    def test_google_adk_imports(self):
        """Test that all required Google ADK modules can be imported"""
        try:
            from google.adk.agents import Agent, LiveRequestQueue
            from google.adk.runners import InMemoryRunner
            from google.genai.types import Content, Part
            from google.adk.agents.run_config import RunConfig
            # If we get here, imports worked
            assert True
        except ImportError as e:
            pytest.fail(f"Failed to import Google ADK modules: {e}")

    def test_basic_agent_creation(self):
        """Test creating a basic ADK agent"""
        from google.adk.agents import Agent
        
        agent = Agent(
            name="test_hello_world_agent",
            model="gemini-2.0-flash-exp",
            description="Simple Hello World agent for testing Issue #3",
            instruction="""
            You are a simple test agent for verifying Google ADK setup. 
            Always respond with 'Hello! ADK is working correctly.' followed by a brief confirmation.
            Keep responses short and positive.
            """
        )
        
        assert agent.name == "test_hello_world_agent"
        assert agent.model == "gemini-2.0-flash-exp"
        assert "hello world" in agent.description.lower()

    @pytest.mark.asyncio
    async def test_basic_conversation_integration(self):
        """
        Integration test: Real conversation with Google ADK
        This tests the complete flow without mocks
        """
        from google.adk.agents import Agent
        from google.adk.runners import InMemoryRunner
        from google.genai.types import Content, Part
        
        # Create a real agent
        agent = Agent(
            name="test_integration_agent",
            model="gemini-2.0-flash-exp",
            description="Integration test agent",
            instruction="""
            You are a test agent for Google ADK integration testing.
            When asked 'Are you working?', always respond with exactly:
            'Yes, ADK integration is working correctly!'
            """
        )
        
        # Create runner and session - use consistent app_name
        app_name = "adk_integration_test"
        runner = InMemoryRunner(agent=agent, app_name=app_name)
        session = await runner.session_service.create_session(
            app_name=app_name,
            user_id="test_user_integration"
        )
        
        assert session.id is not None
        assert session.user_id == "test_user_integration"
        
        # Send a test message
        user_content = Content(
            role="user", 
            parts=[Part.from_text(text="Are you working?")]
        )
        
        # This makes a real API call to Google's servers
        events = runner.run_async(
            user_id=session.user_id,
            session_id=session.id,
            new_message=user_content
        )
        
        # Collect response from events
        response_text = ""
        async for event in events:
            if (hasattr(event, "content") and event.content and 
                event.content.parts):
                for part in event.content.parts:
                    if hasattr(part, "text") and part.text:
                        response_text += part.text
            if hasattr(event, "turn_complete") and event.turn_complete:
                break
        
        # Verify response
        assert len(response_text) > 0
        
        # Verify the agent responded appropriately
        # The response should contain some confirmation 
        # (we can't guarantee exact text due to LLM variability)
        assert any(word in response_text.lower() 
                  for word in ['yes', 'working', 'adk', 'correct'])

    @pytest.mark.asyncio 
    async def test_adk_service_integration(self):
        """Test the actual ADKService class with real API calls"""
        from app.services.adk_service import ADKService, ChatRequest
        
        # Create real ADK service (will make actual API calls)
        service = ADKService()
        
        # Verify service initialized
        assert service.agent is not None
        assert service.app_name == "systemdesign-ai-platform"
        
        # Test health check
        health = service.health_check()
        assert health["configured"] is True
        assert health["status"] == "ready"
        
        # Test real chat
        request = ChatRequest(
            message="Hello! This is an integration test. Please respond with 'Integration test successful!'",
            user_id="test_integration_user"
        )
        
        response = await service.chat(request)
        
        # Verify response
        assert response.success is True
        assert response.session_id is not None
        assert len(response.message) > 0
        assert response.error is None
        
        # The response should indicate success (allowing for LLM variability)
        response_lower = response.message.lower()
        assert any(word in response_lower for word in ['integration', 'test', 'successful', 'hello', 'working'])

    def test_environment_validation(self):
        """Test environment validation logic"""
        from app.services.config import get_settings
        
        settings = get_settings()
        
        # This should not raise an exception if properly configured
        try:
            settings.validate_required_settings()
        except ValueError as e:
            pytest.fail(f"Environment validation failed: {e}")


@pytest.mark.skipif(
    not os.getenv("GOOGLE_API_KEY") and not os.getenv("GOOGLE_GENAI_USE_VERTEXAI") == "TRUE",
    reason="Requires Google API key or Vertex AI configuration for integration testing"
)
class TestADKIntegrationWithAPIKey:
    """Integration tests that require valid API credentials"""
    
    @pytest.mark.asyncio
    async def test_streaming_integration(self):
        """Test the streaming functionality end-to-end"""
        from google.adk.agents import Agent, LiveRequestQueue
        from google.adk.runners import InMemoryRunner
        from google.adk.agents.run_config import RunConfig
        from google.genai.types import Content, Part
        
        # Create agent
        agent = Agent(
            name="streaming_test_agent", 
            model="gemini-2.0-flash-exp",
            instruction="Respond briefly to confirm streaming works"
        )
        
        # Use consistent app_name for runner and session
        app_name = "streaming_test"
        runner = InMemoryRunner(agent=agent, app_name=app_name)
        session = await runner.session_service.create_session(
            app_name=app_name,
            user_id="stream_test_user"
        )
        
        # Test streaming
        live_request_queue = LiveRequestQueue()
        run_config = RunConfig(response_modalities=["TEXT"])
        
        live_events = runner.run_live(
            session=session,
            live_request_queue=live_request_queue,
            run_config=run_config,
        )
        
        # Send message
        user_content = Content(role="user", parts=[Part.from_text(text="Test streaming")])
        live_request_queue.send_content(content=user_content)
        
        # Collect response
        response_text = ""
        event_count = 0
        max_events = 10
        
        async for event in live_events:
            event_count += 1
            if event_count > max_events:
                break
                
            if hasattr(event, "turn_complete") and event.turn_complete:
                break
                
            if hasattr(event, "content") and event.content and event.content.parts:
                for part in event.content.parts:
                    if hasattr(part, "text") and part.text:
                        response_text += part.text
        
        # Clean up
        live_request_queue.close()
        
        # Verify streaming worked
        assert len(response_text.strip()) > 0
        assert event_count > 0


if __name__ == "__main__":
    # Run integration tests when called directly
    print("🧪 Running Google ADK Integration Tests")
    print("=" * 50)
    
    # Use pytest to run the tests
    import subprocess
    import sys
    
    result = subprocess.run([
        sys.executable, "-m", "pytest", __file__, "-v"
    ], cwd=Path(__file__).parent)
    
    if result.returncode == 0:
        print("\n🎉 All integration tests passed!")
        print("✅ Issue #3: Google ADK Basic Setup and Authentication - COMPLETE")
    else:
        print(f"\n⚠️  Some integration tests failed (exit code: {result.returncode})")
        print("❌ Issue #3: Google ADK Basic Setup and Authentication - INCOMPLETE")
    
    sys.exit(result.returncode)