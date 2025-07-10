#!/usr/bin/env python3
"""
Basic Chat Completion - Core Pattern

Demonstrates the foundation patterns that work reliably across all providers:

CORE PATTERNS DEMONSTRATED:
- Single system message approach (Anthropic limitation, works everywhere)
- User/assistant message alternation
- Core parameters (temperature, max_tokens) 
- Clean conversation structure

IMPLEMENTATION APPROACHES:
- LiteLLM unified interface (works with any provider)
- OpenAI native SDK implementation
- Anthropic native SDK implementation

KEY FEATURES:
- Full observability with Langfuse + OpenTelemetry tracing
- Error handling and graceful fallbacks
- Shows provider-specific differences (system message handling)
- Demonstrates why single system messages are the universal pattern

This example establishes the foundation patterns you should reach for first
when building multi-provider LLM applications.
"""

# /// script
# dependencies = ["litellm", "openai", "anthropic", "python-dotenv", "langfuse==2.60.9", "opentelemetry-instrumentation-anthropic", "opentelemetry-instrumentation-openai", "opentelemetry-exporter-otlp"]
# ///

import os

import litellm
from dotenv import load_dotenv
from anthropic import Anthropic
from openai import OpenAI
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.anthropic import AnthropicInstrumentor
from opentelemetry.instrumentation.openai import OpenAIInstrumentor
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor

from langfuse import Langfuse

# Load environment variables
load_dotenv()

# Sets the global default tracer provider
trace_provider = TracerProvider()
trace_provider.add_span_processor(SimpleSpanProcessor(OTLPSpanExporter()))
trace.set_tracer_provider(trace_provider)

AnthropicInstrumentor().instrument()
OpenAIInstrumentor().instrument()
litellm.callbacks = ["langfuse"]

# Note: Langfuse will show the messages you send to LiteLLM, 
# not the transformed messages actually sent to providers.
# For Anthropic, system messages get moved from messages[] to system parameter,
# but this transformation won't be visible in Langfuse traces.


def litellm_basic_chat():
    """Basic chat using LiteLLM - works with any provider"""
    
    print("=== LiteLLM Basic Chat ===")
    
    # Test with different providers
    models = ["gpt-4o-mini", "claude-3-haiku-20240307"]
    
    for model in models:
        try:
            print(f"\n--- Testing {model} ---")
            
            messages = [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "What are the core features that work across all LLM providers?"}
            ]
            
            response = litellm.completion(
                model=model,
                messages=messages,
                temperature=0.7,
                max_tokens=150
            )
            
            print(f"Response: {response.choices[0].message.content}")
            
        except Exception as e:
            print(f"Error with {model}: {e}")


def openai_basic_chat():
    """Basic chat using OpenAI SDK directly"""
    try:
        print("\n=== OpenAI SDK Basic Chat ===")
        
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "What are the core features that work across all LLM providers?"}
            ],
            temperature=0.7,
            max_tokens=150
        )
        
        print(f"Response: {response.choices[0].message.content}")
        
    except Exception as e:
        print(f"OpenAI SDK error: {e}")


def anthropic_basic_chat():
    """Basic chat using Anthropic SDK directly"""
    try:
        print("\n=== Anthropic SDK Basic Chat ===")
        
        client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        
        # Note: Anthropic uses different message format
        response = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=150,
            temperature=0.7,
            system="You are a helpful assistant.",  # System message separate
            messages=[
                {"role": "user", "content": "What are the core features that work across all LLM providers?"}
            ]
        )

        # LiteLLM handles system messages differently, so they need to convert them:
        #
        # 1. Identifies all system messages in the message list (role == "system")
        # 2. Converts them to Anthropic's system message format (AnthropicSystemMessageContent)
        # 3. Removes the system messages from the original messages list
        # 4. Returns the converted system messages as a separate list
        #
        # The key merging logic is that it processes all system messages sequentially, converting
        # each one to Anthropic format andcollecting them into anthropic_system_message_list, then
        # removes them from the original messages using messages.pop(idx) in reverse order to avoid
        # index shifting issues.
        
        print(f"Response: {response.content[0].text}")
        
    except Exception as e:
        print(f"Anthropic SDK error: {e}")

def main():
    """Run all basic chat examples"""
    print("Basic Chat Completion Examples")
    print("="*50)

    langfuse = Langfuse()
    
    # LiteLLM approach (multi-provider)
    litellm_basic_chat()
    
    # Native SDK approaches
    openai_basic_chat()
    anthropic_basic_chat()

    langfuse.flush()

if __name__ == "__main__":
    main()
