# Portable LLM

**The features that work reliably across all LLM providers - and why you should reach for them first.**

## Overview

While debugging LLM streaming bugs, I discovered that mixing provider-specific features creates unexpected complexity. This repository shows the core patterns that work universally, helping you build more predictable multi-provider applications.

**Key insight**: Sometimes the best solution isn't adding more compatibility - it's using the patterns that already work everywhere.

## Why I Started Questioning Compatibility

While fixing bugs in LiteLLM's streaming + response_format + tools combination, I discovered:

**The bugs**: Tool calls incorrectly converted to content, wrong finish_reason breaking OpenAI compatibility  
**The deeper issue**: LiteLLM needs complex logic to simulate OpenAI's response_format on Anthropic's tool-first architecture  
**The insight**: Instead of fixing compatibility edge cases, we could use tool calls - which work natively on both platforms  

**Takeaway**: Sometimes the "solution" is using simpler patterns that don't need compatibility shims.

## The Core Patterns

### ✅ Reach for These First
- **Tool calls with JSON schema** - universal structured output that works natively on both platforms
- **Basic chat completions** - messages array works everywhere with consistent behavior
- **Single system messages** - Anthropic limitation becomes universal pattern
- **User/assistant alternation** - clean conversation structure across providers
- **Standard parameters** - temperature, max_tokens, top_p work consistently
- **Pydantic models** - clean schema definition and parsing for structured data

### 🤔 Think Twice About These
- **response_format** - creates architectural mismatches, tool calls are more universal
- **Multiple system messages** - Anthropic doesn't support, breaks compatibility
- **Provider-specific parameters** - creates branching logic and compatibility complexity
- **Complex streaming + tools combinations** - edge cases and compatibility shims
- **Advanced reasoning modes** - provider-specific, requires explicit branching

### 🎯 The Mindset Shift
1. **Default to core patterns** - they're simpler and more predictable
2. **Use single system messages** - Anthropic limitation, works everywhere
3. **Test with streaming enabled** - catches compatibility issues early

## Setup

1. Install UV (if not already installed):
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

2. Copy the environment template:
```bash
cp .env.example .env
```

3. Add your API keys to `.env`:
```
OPENAI_API_KEY=your-openai-key
ANTHROPIC_API_KEY=your-anthropic-key
```

## Examples

Two comprehensive examples that demonstrate the core patterns:

### **Basic Chat Completion** - `uv run examples/basic_chat.py`
The foundation patterns that work across all providers:
- Single system message approach
- User/assistant message alternation  
- Core parameters (temperature, max_tokens)
- Both LiteLLM unified and native SDK implementations
- Observability with Langfuse + OpenTelemetry tracing

### **Tool Calls vs Response Format** - `uv run examples/tool_calls_vs_response_format.py`
A comprehensive comparison showing how each provider handles structured output:

**Anthropic Examples:**
- **Tool only** (`tool_choice: "auto"`) - Let model decide whether to use tools
- **JSON mode** (`tool_choice: {"type": "tool", "name": "..."}`) - Force structured output via specific tool  
- **Tools + JSON mode** (`tool_choice: "any"`) - Model can choose between function calling and structured output

**OpenAI Examples:**
- **Agent loop** with tools + response_format combined
- Loops until `finish_reason == "stop"` (natural completion)
- Shows how to combine function calling with structured final output

**LiteLLM Examples:**
- **Cross-provider agent loops** using unified tool interface
- Loops until specific tool is called (`weather_report`)
- Demonstrates consistent tool calling across providers

**Key Features:**
- Realistic weather agent loop patterns with multiple API calls
- Pydantic models for clean schema definition and parsing
- Full observability with Langfuse + OpenTelemetry tracing
- Error handling and safety breaks
- Demonstrates why tool calls provide better cross-provider compatibility than response_format

## Best Practices

1. **Design for the most restrictive provider** (Anthropic) to ensure universal compatibility
2. **Use tool calls as the universal language** for structured output across all providers
3. **Single system messages only** - avoid multiple system messages that break on Anthropic
4. **Test with streaming enabled** to catch compatibility inconsistencies early
5. **Use Pydantic models** for clean schema definition and automatic validation
6. **Implement proper agent loops** with termination conditions and safety breaks
7. **Add observability from the start** - Langfuse + OpenTelemetry make debugging easier
8. **Keep provider-specific code isolated** and clearly documented when necessary

## Contributing

Feel free to open issues or submit PRs with additional patterns or improvements to existing examples.
