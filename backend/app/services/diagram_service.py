import base64
import logging
import os
import tempfile
import uuid
from typing import Optional

from google.adk.agents.llm_agent import LlmAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.tools.mcp_tool.mcp_toolset import (
    MCPToolset,
    StdioConnectionParams,
    StdioServerParameters
)
from google.genai import types

from app.models.diagram import (
    DiagramGenerationRequest,
    DiagramGenerationResponse,
    DiagramType
)
from app.services.adk_service import ADKService
from app.services.whiteboard_service import WhiteboardService
from app.models.whiteboard import PNGUploadRequest

logger = logging.getLogger(__name__)


class DiagramService:
    def __init__(
        self,
        adk_service: ADKService,
        whiteboard_service: WhiteboardService
    ):
        self.adk_service = adk_service
        self.whiteboard_service = whiteboard_service
        self.session_service = InMemorySessionService()
        self._mcp_agent: Optional[LlmAgent] = None
        self._mcp_runner: Optional[Runner] = None
        self._mcp_toolset: Optional[MCPToolset] = None

    async def initialize_mcp(self):
        """Initialize the MCP toolset and agent for Mermaid diagrams."""
        if self._mcp_agent is not None:
            return  # Already initialized

        logger.info("Initializing MCP toolset for Mermaid diagram generation")

        try:
            # Set up environment with Chrome path for Puppeteer globally
            chrome_path = (
                "/Users/deepak/.cache/puppeteer/chrome/mac-139.0.7258.66/"
                "chrome-mac-x64/Google Chrome for Testing.app/Contents/"
                "MacOS/Google Chrome for Testing"
            )
            if os.path.exists(chrome_path):
                os.environ['PUPPETEER_EXECUTABLE_PATH'] = chrome_path
                logger.info(f"MCP initialization using Chrome path: {chrome_path}")
            
            # Create MCPToolset with stdio connection to mermaid-mcp-server
            # Based on ADK docs, MCPToolset manages its own lifecycle
            self._mcp_toolset = MCPToolset(
                connection_params=StdioConnectionParams(
                    server_params=StdioServerParameters(
                        command='npx',
                        args=['-y', '@peng-shawn/mermaid-mcp-server'],
                    ),
                ),
                tool_filter=['generate']  # Only use the generate tool
            )

            # Create an agent with the MCP toolset
            instruction = (
                "You are a Mermaid diagram renderer. "
                "Use the generate tool to create PNG images from Mermaid code."
            )
            self._mcp_agent = LlmAgent(
                model='gemini-2.0-flash-exp',
                name='mermaid_renderer',
                instruction=instruction,
                tools=[self._mcp_toolset]
            )

            # Create runner for the MCP agent
            self._mcp_runner = Runner(
                app_name='diagram_service',
                agent=self._mcp_agent,
                session_service=self.session_service,
            )

            logger.info("MCP toolset initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize MCP toolset: {e}")
            # Reset on failure
            self._mcp_agent = None
            self._mcp_runner = None
            self._mcp_toolset = None
            raise

    async def cleanup_mcp(self):
        """Clean up MCP resources."""
        if self._mcp_toolset:
            logger.info("Cleaning up MCP resources")
            # MCPToolset should handle its own cleanup
            self._mcp_agent = None
            self._mcp_runner = None
            self._mcp_toolset = None

    async def generate_diagram(
        self, request: DiagramGenerationRequest
    ) -> DiagramGenerationResponse:
        logger.info(
            f"Generating diagram for user '{request.user_id}' "
            f"with description: '{request.system_description}'"
        )

        # 1. Generate Mermaid code from description using LLM
        result = await self.adk_service.generate_mermaid_code(
            request.system_description,
            request.diagram_type,
            request.session_id
        )
        mermaid_code, model_used, tokens_used, cost_estimate = result
        logger.info(
            f"Generated Mermaid code for user '{request.user_id}':\n"
            f"{mermaid_code}"
        )

        # 2. Render Mermaid code to PNG using mermaid-mcp-server
        png_data = await self._render_mermaid_to_png(mermaid_code)

        # 3. Store PNG as an artifact using WhiteboardService
        upload_request = PNGUploadRequest(
            png_data=base64.b64encode(png_data).decode("utf-8"),
            user_id=request.user_id,
            session_id=request.session_id,
        )
        upload_response = await self.whiteboard_service.upload_png(
            upload_request
        )
        logger.info(
            f"Stored diagram PNG as artifact with ID: "
            f"{upload_response.artifact_id}"
        )

        # 4. Create and return the response
        diagram_id = str(uuid.uuid4())
        response = DiagramGenerationResponse(
            diagram_id=diagram_id,
            mermaid_code=mermaid_code,
            png_artifact_id=upload_response.artifact_id,
            model_used=model_used,
            tokens_used=tokens_used,
            cost_estimate=cost_estimate,
        )

        return response

    async def _generate_mermaid_code(
        self,
        system_description: str,
        diagram_type: DiagramType
    ) -> tuple[str, str, int, float]:
        # This is now handled by the ADK service
        raise NotImplementedError(
            "This method is deprecated. Use ADKService.generate_mermaid_code."
        )

    async def _render_mermaid_to_png(self, mermaid_code: str) -> bytes:
        """Renders Mermaid code to PNG using ADK MCPToolset integration."""
        logger.info("Rendering Mermaid code to PNG using MCP server")

        # Ensure MCP is initialized - if it fails, fall back to mock
        try:
            await self.initialize_mcp()
        except Exception as e:
            logger.warning(f"MCP initialization failed during rendering: {e}")
            logger.info("Falling back to informational PNG generation")
            return self._create_mock_png(mermaid_code)

        if not self._mcp_agent or not self._mcp_runner:
            logger.warning(
                "MCP agent not available, falling back to informational PNG"
            )
            return self._create_mock_png(mermaid_code)

        try:
            # Create a session for this rendering operation
            session = await self.session_service.create_session(
                state={},
                app_name='diagram_service',
                user_id='mermaid_renderer'
            )

            # Create a unique output filename and directory
            output_filename = f"diagram_{uuid.uuid4().hex}"
            output_dir = tempfile.gettempdir()

            # Clean the Mermaid code by removing YAML config that causes issues
            cleaned_code = self._clean_mermaid_code(mermaid_code)
            
            # Prepare the prompt for the MCP agent to use the generate tool
            prompt = (
                f"Please use the generate tool to create a PNG image "
                f"from this Mermaid code:\n\n"
                f"```mermaid\n{cleaned_code}\n```\n\n"
                f"Use these parameters:\n"
                f"- code: {cleaned_code}\n"
                f"- outputFormat: png\n"
                f"- name: {output_filename}\n"
                f"- folder: {output_dir}\n"
                f"- theme: default\n"
                f"- backgroundColor: white"
            )

            logger.info("Sending Mermaid code to MCP agent for rendering")
            expected_path = os.path.join(output_dir, output_filename + '.png')
            logger.info(f"Output will be saved as: {expected_path}")

            # Create the message content
            content = types.Content(
                role='user',
                parts=[types.Part(text=prompt)]
            )

            # Use the direct MCP approach that we know works
            try:
                return await self._direct_mcp_generate(cleaned_code, output_filename, output_dir)
            except Exception as e:
                logger.error(f"Direct MCP generation failed: {e}")
                return self._create_mock_png(mermaid_code)

            # Check if the PNG file was created
            png_file_path = os.path.join(output_dir, f"{output_filename}.png")
            if not os.path.exists(png_file_path):
                logger.error(f"PNG file not found at {png_file_path}")
                # Fall back to mock implementation
                return self._create_mock_png(mermaid_code)

            # Read the generated PNG file
            with open(png_file_path, 'rb') as f:
                png_data = f.read()

            logger.info(
                f"Successfully generated PNG via MCP. "
                f"Size: {len(png_data)} bytes"
            )

            # Clean up the temporary file
            try:
                os.remove(png_file_path)
            except OSError:
                logger.warning(
                    f"Could not remove temporary file: {png_file_path}"
                )

            return png_data

        except Exception as e:
            logger.error(f"Error rendering Mermaid diagram via MCP: {e}")
            logger.info("Trying direct mermaid-cli fallback before mock PNG")
            
            # Try direct mermaid-cli as backup
            try:
                direct_png = await self._try_direct_mermaid_cli(mermaid_code)
                if direct_png:
                    return direct_png
            except Exception as cli_error:
                logger.warning(f"Direct mermaid-cli also failed: {cli_error}")
            
            logger.info("Falling back to informational PNG generation")
            return self._create_mock_png(mermaid_code)

    async def _process_mcp_events(self, events_async) -> str:
        """Process MCP events and return the final response."""
        final_response = ""
        async for event in events_async:
            logger.debug(f"MCP Event: {event}")
            # The events will contain tool calls and responses
            if hasattr(event, 'message') and event.message:
                final_response += str(event.message)
        return final_response

    def _clean_mermaid_code(self, mermaid_code: str) -> str:
        """Clean Mermaid code by removing problematic YAML config sections."""
        lines = mermaid_code.split('\n')
        cleaned_lines = []
        in_yaml_config = False
        
        for line in lines:
            # Check for YAML front matter start
            if line.strip() == '---':
                if not in_yaml_config:
                    in_yaml_config = True
                    continue  # Skip the opening ---
                else:
                    in_yaml_config = False
                    continue  # Skip the closing ---
            
            # Skip lines inside YAML config
            if in_yaml_config:
                continue
                
            # Keep all other lines
            cleaned_lines.append(line)
        
        cleaned_code = '\n'.join(cleaned_lines).strip()
        
        if cleaned_code != mermaid_code:
            logger.info("Removed YAML config section from Mermaid code for compatibility")
            
        return cleaned_code

    async def _direct_mcp_generate(self, cleaned_code: str, output_filename: str, output_dir: str) -> bytes:
        """Use direct MCP server communication that we know works."""
        import subprocess
        import json
        import time
        
        logger.info("Using direct MCP server communication")
        
        # Set up environment 
        env = os.environ.copy()
        chrome_path = (
            "/Users/deepak/.cache/puppeteer/chrome/mac-139.0.7258.66/"
            "chrome-mac-x64/Google Chrome for Testing.app/Contents/"
            "MacOS/Google Chrome for Testing"
        )
        if os.path.exists(chrome_path):
            env['PUPPETEER_EXECUTABLE_PATH'] = chrome_path
        
        # Start MCP server
        process = subprocess.Popen([
            'npx', '-y', '@peng-shawn/mermaid-mcp-server'
        ], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=env)
        
        try:
            # Initialize
            init_req = {
                "jsonrpc": "2.0", "id": 1, "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05", "capabilities": {},
                    "clientInfo": {"name": "diagram-service", "version": "1.0.0"}
                }
            }
            process.stdin.write(json.dumps(init_req) + '\n')
            process.stdin.flush()
            process.stdout.readline()  # Read init response
            
            # Generate
            gen_req = {
                "jsonrpc": "2.0", "id": 2, "method": "tools/call",
                "params": {
                    "name": "generate",
                    "arguments": {
                        "code": cleaned_code,
                        "outputFormat": "png", 
                        "name": output_filename,
                        "folder": output_dir,
                        "theme": "default",
                        "backgroundColor": "white"
                    }
                }
            }
            
            logger.info("Sending generate request to MCP server")
            process.stdin.write(json.dumps(gen_req) + '\n')
            process.stdin.flush()
            
            # Wait for file creation
            expected_png = os.path.join(output_dir, f"{output_filename}.png")
            start_time = time.time()
            
            while time.time() - start_time < 15:  # 15 second timeout
                if os.path.exists(expected_png):
                    with open(expected_png, 'rb') as f:
                        png_data = f.read()
                    
                    logger.info(f"Successfully generated PNG via direct MCP: {len(png_data)} bytes")
                    
                    # Cleanup
                    try:
                        os.remove(expected_png)
                    except OSError:
                        pass
                        
                    return png_data
                    
                if process.poll() is not None:
                    break
                    
                time.sleep(0.5)
            
            # If we get here, it failed
            raise Exception("PNG file not created within timeout")
            
        finally:
            process.terminate()
            try:
                process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                process.kill()

    async def _try_direct_mermaid_cli(self, mermaid_code: str) -> Optional[bytes]:
        """Try using mermaid-cli directly as a fallback."""
        import subprocess
        
        try:
            # Create temporary files
            input_file = tempfile.NamedTemporaryFile(mode='w', suffix='.mmd', delete=False)
            output_file = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
            
            # Write mermaid code to temp file
            input_file.write(mermaid_code)
            input_file.close()
            output_file.close()
            
            # Set up environment with Chrome path for Puppeteer
            env = os.environ.copy()
            chrome_path = "/Users/deepak/.cache/puppeteer/chrome/mac-139.0.7258.66/chrome-mac-x64/Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing"
            if os.path.exists(chrome_path):
                env['PUPPETEER_EXECUTABLE_PATH'] = chrome_path
                logger.info(f"Using Chrome path: {chrome_path}")
            
            # Try to run mermaid-cli with Chrome path
            result = subprocess.run([
                'npx', '@mermaid-js/mermaid-cli', 
                '-i', input_file.name, 
                '-o', output_file.name,
                '--puppeteerConfig', '{"headless":true,"args":["--no-sandbox","--disable-setuid-sandbox"]}'
            ], capture_output=True, text=True, timeout=30, env=env)
            
            if result.returncode == 0 and os.path.exists(output_file.name):
                # Read the generated PNG
                with open(output_file.name, 'rb') as f:
                    png_data = f.read()
                    
                logger.info(f"Successfully generated PNG via direct mermaid-cli: {len(png_data)} bytes")
                
                # Cleanup
                try:
                    os.unlink(input_file.name)
                    os.unlink(output_file.name)
                except:
                    pass
                    
                return png_data
            else:
                logger.warning(f"mermaid-cli failed: {result.stderr}")
                return None
                
        except Exception as e:
            logger.warning(f"Direct mermaid-cli attempt failed: {e}")
            return None
        finally:
            # Cleanup in case of error
            try:
                if 'input_file' in locals():
                    os.unlink(input_file.name)
                if 'output_file' in locals():
                    os.unlink(output_file.name)
            except:
                pass

    def _create_mock_png(self, mermaid_code: str = "") -> bytes:
        """Create a text-based diagram as PNG fallback."""
        try:
            from PIL import Image, ImageDraw, ImageFont
            import io
            
            # Create a white canvas
            width, height = 800, 600
            img = Image.new('RGB', (width, height), color='white')
            draw = ImageDraw.Draw(img)
            
            # Try to use a default font
            try:
                font = ImageFont.truetype("Arial.ttf", 14)
                title_font = ImageFont.truetype("Arial.ttf", 18)
            except:
                font = ImageFont.load_default()
                title_font = font
            
            # Draw title
            title = "🎨 Mermaid Diagram Generated"
            draw.text((20, 20), title, fill='black', font=title_font)
            
            # Draw explanation
            explanation = [
                "✅ Dynamic diagram code successfully generated by AI!",
                "",
                "📋 Copy the Mermaid code below to visualize:",
                "• Paste into https://mermaid.live/",
                "• Use in GitHub Markdown",
                "• Import into Miro, Lucidchart, etc.",
                "",
                "🔧 Note: PNG rendering temporarily uses fallback"
            ]
            
            y_pos = 60
            for line in explanation:
                draw.text((20, y_pos), line, fill='black', font=font)
                y_pos += 20
            
            # Draw Mermaid code (first 20 lines)
            if mermaid_code:
                y_pos += 20
                draw.text((20, y_pos), "💻 Generated Mermaid Code:", fill='black', font=title_font)
                y_pos += 30
                
                lines = mermaid_code.split('\n')[:20]  # First 20 lines
                for line in lines:
                    if y_pos < height - 30:  # Leave space at bottom
                        draw.text((20, y_pos), line[:80], fill='#333333', font=font)  # Truncate long lines
                        y_pos += 16
                
                if len(lines) > 20:
                    draw.text((20, y_pos), "... (code continues)", fill='#666666', font=font)
            
            # Save to bytes
            png_buffer = io.BytesIO()
            img.save(png_buffer, format='PNG')
            png_data = png_buffer.getvalue()
            
            logger.info(f"Created informational PNG with Mermaid code. Size: {len(png_data)} bytes")
            return png_data
            
        except ImportError:
            # Fallback to minimal PNG if PIL is not available
            mock_png_data = bytes([
                0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A,  # PNG signature
                0x00, 0x00, 0x00, 0x0D,  # IHDR chunk length
                0x49, 0x48, 0x44, 0x52,  # IHDR
                0x00, 0x00, 0x00, 0x01,  # Width: 1
                0x00, 0x00, 0x00, 0x01,  # Height: 1
                0x08, 0x06, 0x00, 0x00, 0x00,  # Bit depth, color type, etc.
                0x1F, 0x15, 0xC4, 0x89,  # CRC
                0x00, 0x00, 0x00, 0x0B,  # IDAT chunk length
                0x49, 0x44, 0x41, 0x54,  # IDAT
                # Compressed data
                0x78, 0x9C, 0x63, 0x00, 0x01, 0x00, 0x00, 0x05, 0x00, 0x01,
                0x0D, 0x0A, 0x2D, 0xB4,  # CRC
                0x00, 0x00, 0x00, 0x00,  # IEND chunk length
                0x49, 0x45, 0x4E, 0x44,  # IEND
                0xAE, 0x42, 0x60, 0x82   # CRC
            ])
            logger.info(f"PIL not available, created minimal PNG fallback. Size: {len(mock_png_data)} bytes")
            return mock_png_data
