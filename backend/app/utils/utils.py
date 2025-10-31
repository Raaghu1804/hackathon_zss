from google.genai import types


# ANSI color codes for terminal output
class Colors:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"

    # Foreground colors
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"

    # Background colors
    BG_BLACK = "\033[40m"
    BG_RED = "\033[41m"
    BG_GREEN = "\033[42m"
    BG_YELLOW = "\033[43m"
    BG_BLUE = "\033[44m"
    BG_MAGENTA = "\033[45m"
    BG_CYAN = "\033[46m"
    BG_WHITE = "\033[47m"


async def display_state(
    session_service, app_name, user_id, session_id, label="Current State"
):
    """Display the current session state in a formatted way."""
    try:
        session = await session_service.get_session(
            app_name=app_name, user_id=user_id, session_id=session_id
        )

        # Format the output with clear sections
        print(f"\n{'-' * 10} {label} {'-' * 10}")

        # Handle the user name
        user_name = session.state.get("user_name", "Unknown")
        print(f"👤 User: {user_name}")

        # Handle reminders
        reminders = session.state.get("files", [])
        if reminders:
            print("📝 Files:")
            print(reminders)
        else:
            print("📝 Files: None")

        print("-" * (22 + len(label)))
    except Exception as e:
        print(f"Error displaying state: {e}")


async def process_agent_response(event, websocket_manager=None):
    """Process and display agent response events, with optional WebSocket streaming."""
    # Log basic event info
    print(f"Event ID: {event.id}, Author: {event.author}")

    # Track intermediate messages for WebSocket
    intermediate_messages = []

    # Check for specific parts first
    has_specific_part = False
    if event.content and event.content.parts:
        for part in event.content.parts:
            if hasattr(part, "executable_code") and part.executable_code:
                # Access the actual code string via .code
                print(
                    f"  Debug: Agent generated code:\n```python\n{part.executable_code.code}\n```"
                )
                has_specific_part = True
            elif hasattr(part, "code_execution_result") and part.code_execution_result:
                # Access outcome and output correctly
                print(
                    f"  Debug: Code Execution Result: {part.code_execution_result.outcome} - Output:\n{part.code_execution_result.output}"
                )
                has_specific_part = True
            elif hasattr(part, "tool_response") and part.tool_response:
                # Print tool response information
                tool_output = str(part.tool_response.output)
                print(f"  Tool Response: {tool_output}")

                # Add tool response to intermediate messages for WebSocket
                intermediate_messages.append({
                    "type": "tool_response",
                    "agent": event.author,
                    "message": f"Tool executed: {tool_output[:200]}..."  # Truncate long outputs
                })
                has_specific_part = True
            elif hasattr(part, "function_call") and part.function_call:
                # Capture function/tool calls
                func_name = part.function_call.name
                print(f"  Function Call: {func_name}")

                # Add function call to intermediate messages for WebSocket
                intermediate_messages.append({
                    "type": "tool_call",
                    "agent": event.author,
                    "message": f"🔧 {event.author} → Calling tool: {func_name}"
                })
                has_specific_part = True
            # Also print any text parts found in any event for debugging
            elif hasattr(part, "text") and part.text and not part.text.isspace():
                text_content = part.text.strip()
                print(f"  Text: '{text_content}'")

                # Add intermediate text to messages if not final response
                if not event.is_final_response():
                    intermediate_messages.append({
                        "type": "intermediate_text",
                        "agent": event.author,
                        "message": text_content[:300]  # Truncate long messages
                    })

    # Broadcast intermediate messages to WebSocket
    if websocket_manager and intermediate_messages:
        for msg in intermediate_messages:
            await websocket_manager.broadcast({
                "type": "agent_communication",
                "event": msg["type"],
                "agent": msg["agent"],
                "message": msg["message"],
                "is_final": False
            })

    # Check for final response after specific parts
    final_response = None
    if event.is_final_response():
        if (
            event.content
            and event.content.parts
            and hasattr(event.content.parts[0], "text")
            and event.content.parts[0].text
        ):
            final_response = event.content.parts[0].text.strip()
            # Use colors and formatting to make the final response stand out
            print(
                f"\n{Colors.BG_BLUE}{Colors.WHITE}{Colors.BOLD}╔══ AGENT RESPONSE ═════════════════════════════════════════{Colors.RESET}"
            )
            print(f"{Colors.CYAN}{Colors.BOLD}{final_response}{Colors.RESET}")
            print(
                f"{Colors.BG_BLUE}{Colors.WHITE}{Colors.BOLD}╚═════════════════════════════════════════════════════════════{Colors.RESET}\n"
            )
        else:
            print(
                f"\n{Colors.BG_RED}{Colors.WHITE}{Colors.BOLD}==> Final Agent Response: [No text content in final event]{Colors.RESET}\n"
            )

    return final_response


async def call_agent_async(runner, user_id, session_id, query, websocket_manager=None):
    """Call the agent asynchronously with the user's query.

    Args:
        runner: The ADK runner
        user_id: User ID for the session
        session_id: Session ID
        query: The query string to send to agents
        websocket_manager: Optional WebSocket manager to stream agent responses in real-time
    """
    content = types.Content(role="user", parts=[types.Part(text=query)])
    print(
        f"\n{Colors.BG_GREEN}{Colors.BLACK}{Colors.BOLD}--- Running Query: {query} ---{Colors.RESET}"
    )
    final_response_text = None

    # Display state before processing
    await display_state(
        runner.session_service,
        runner.app_name,
        user_id,
        session_id,
        "State BEFORE processing",
    )

    # Notify via WebSocket that ADK processing has started
    if websocket_manager:
        await websocket_manager.broadcast({
            "type": "agent_communication",
            "event": "started",
            "message": "🤖 Google ADK Multi-Agent System activated - analyzing anomaly..."
        })

    # try:
    async for event in runner.run_async(
        user_id=user_id, session_id=session_id, new_message=content
    ):
        # Process each event (now includes WebSocket streaming of intermediate steps)
        response = await process_agent_response(event, websocket_manager=websocket_manager)

        # Stream final agent responses via WebSocket
        if websocket_manager and response:
            agent_name = event.author if hasattr(event, 'author') else "Agent"
            await websocket_manager.broadcast({
                "type": "agent_communication",
                "event": "agent_response",
                "agent": agent_name,
                "message": response,
                "is_final": event.is_final_response() if hasattr(event, 'is_final_response') else False
            })

        if response:
            final_response_text = response
    # except Exception as e:
    #     print(f"Error during agent call: {e}")

    # Display state after processing the message
    await display_state(
        runner.session_service,
        runner.app_name,
        user_id,
        session_id,
        "State AFTER processing",
    )

    # Notify completion via WebSocket
    if websocket_manager:
        await websocket_manager.broadcast({
            "type": "agent_communication",
            "event": "completed",
            "message": "✅ Multi-agent analysis completed"
        })

    return final_response_text