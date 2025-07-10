# YouTube Video: "Core LLM Features: What Works Across All Providers"

## Hook (1 min)
"I just submitted a PR to LiteLLM that helps bridge the gap between OpenAI and Anthropic for tools, response_format, and streaming. But now I'm wondering if that was the wrong move. Let me show you what I learned while creating this fix - and why it made me question the whole approach."

## What I Discovered: The response_format Architecture Mismatch (8 min)

### The Bugs I Discovered
While working on LiteLLM streaming, I found two real bugs when using `response_format` + tools + streaming:

**Bug 1: All tool calls became content**
- ALL tool calls were incorrectly converted to content chunks
- Should only convert the internal response_format tool, not your actual tools

**Bug 2: Wrong finish_reason**  
- Response_format tools returned `finish_reason="tool_calls"` instead of `"stop"`
- This breaks OpenAI API compatibility - response_format should always end with "stop"

### What I Learned: Provider Philosophy Differences
- **OpenAI**: Has native `response_format` for JSON output separate from tools
- **Anthropic**: Tool-first architecture - uses tools for ALL structured output (no native JSON mode)
- **Compatibility complexity**: Simulating OpenAI's `response_format` on Anthropic requires hidden tool calls
- **Streaming constraint**: Can't wait to count total tools before streaming starts

### My Realization: Maybe We Shouldn't Bridge Everything  
I fixed these bugs, but debugging them showed me the underlying complexity. LiteLLM has to simulate OpenAI's `response_format` on Anthropic using hidden tool calls, then carefully manage which tools become content and which stay as tool calls, all while maintaining the right finish_reason.

My PR fixed the technical issues, but it made me realize: maybe we shouldn't force this compatibility in the first place.

### The Better Solution: Use Tool Calls Instead
**Why tool calls win**: Universal support, aligns with both provider architectures, no compatibility shims needed

*[Live demo of this principle using examples/tool_calls_vs_response_format.py]*

## What This Taught Me About Multi-Provider Development (3 min)

### The Core Features That Actually Work Everywhere
From fixing these bugs, I learned there's a small set of features that work reliably across all providers:
- **Tool calls with JSON schema** - native on both OpenAI and Anthropic
- **Basic chat completions** - messages array works everywhere
- **Streaming responses** - supported universally 
- **Standard parameters** - temperature, max_tokens, etc.

### The Universal Patterns
1. Use tool calls for structured output (not response_format)
2. Follow user/assistant alternation (Anthropic requirement)
3. Use single system messages
4. Test with streaming enabled to validate compatibility
5. Keep provider-specific code isolated when needed

## Live Demo: Tool Calls vs Response Format (8 min)

*[Code walkthrough of examples/tool_calls_vs_response_format.py]*

### Anthropic Examples - The Tool-First Architecture
- **Tool only** (`tool_choice: "auto"`) - Let model decide whether to use tools
- **JSON mode** (`tool_choice: {"type": "tool", "name": "..."}`) - Force structured output via specific tool  
- **Tools + JSON mode** (`tool_choice: "any"`) - Model can choose between function calling and structured output

### OpenAI Examples - Tools + Response Format Combined  
- **Agent loop** with tools + response_format working together
- Loops until `finish_reason == "stop"` (natural completion)
- Shows how to combine function calling with structured final output

### LiteLLM Examples - Unified Interface
- **Cross-provider agent loops** using consistent tool interface
- Loops until specific tool is called (`weather_report`)
- Same code works across providers, handles differences automatically

### Key Insights from the Demo
- Tool calls provide consistent behavior across providers
- Agent loops show realistic multi-step patterns
- Pydantic models give clean schema definition and parsing
- Response_format creates architectural mismatches

## Key Takeaways & Action Items (2 min)

### What I Learned
- **Compatibility layers create complexity** - fixing my bugs revealed how much hidden logic is needed
- **Tool calls are the universal language** for structured output across all providers
- **Core features provide a reliable foundation** - less debugging, more predictable behavior

### What You Should Do
1. **Audit your code** for response_format usage - replace with tool calls
2. **Test with streaming enabled** to catch compatibility issues early  
3. **Design for the most restrictive provider** (Anthropic) to ensure universal compatibility
4. **Explore the examples** - Check out `examples/basic_chat.py` for foundation patterns

**Bottom Line**: Sometimes the best fix isn't adding more compatibility - it's using the patterns that already work everywhere.

### Repository & Additional Resources
- Full examples with observability (Langfuse + OpenTelemetry)
- `examples/basic_chat.py` - Foundation patterns for self-study
- `examples/tool_calls_vs_response_format.py` - Everything we demonstrated today
- Best practices guide for multi-provider development

---

**Total Runtime**: ~16 minutes
