#!/usr/bin/env python3
"""
Tool Calls vs Response Format - Provider Comparison

A comprehensive comparison showing how each provider handles structured output:

ANTHROPIC EXAMPLES:
- Tool only (tool_choice: "auto") - Let model decide whether to use tools
- JSON mode (tool_choice: {"type": "tool", "name": "..."}) - Force structured output via specific tool  
- Tools + JSON mode (tool_choice: "any") - Model can choose between function calling and structured output

OPENAI EXAMPLES:
- Agent loop with tools + response_format combined
- Loops until finish_reason == "stop" (natural completion)
- Shows how to combine function calling with structured final output

LITELLM EXAMPLES:
- Cross-provider agent loops using unified tool interface
- Loops until specific tool is called (weather_report)
- Demonstrates consistent tool calling across providers

KEY FEATURES:
- Realistic weather agent loop patterns with multiple API calls
- Pydantic models for clean schema definition and parsing
- Full observability with Langfuse + OpenTelemetry tracing
- Error handling and safety breaks
- Demonstrates why tool calls provide better cross-provider compatibility than response_format

This example shows why tool calls are the "universal language" for structured output,
while response_format creates architectural mismatches between providers.
"""

# /// script
# dependencies = ["litellm", "openai", "anthropic", "python-dotenv", "langfuse==2.60.9", "opentelemetry-instrumentation-anthropic", "opentelemetry-instrumentation-openai", "opentelemetry-exporter-otlp", "pydantic"]
# ///

import os
import json
import litellm
from anthropic import Anthropic
from openai import OpenAI
from pydantic import BaseModel
from dotenv import load_dotenv
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

# Instrument the SDKs
AnthropicInstrumentor().instrument()
OpenAIInstrumentor().instrument()
litellm.callbacks = ["langfuse"]

# Pydantic models for structured output
class CurrentWeather(BaseModel):
    location: str | None = None
    temperature: str | None = None
    unit: str | None = None

class WeatherReport(BaseModel):
    current_weather: list[CurrentWeather] | None = None

# Example dummy function hard coded to return the same weather
# In production, this could be your backend API or an external API
def get_current_weather(location, unit="fahrenheit"):
    """Get the current weather in a given location"""
    if "tokyo" in location.lower():
        return json.dumps({"location": "Tokyo", "temperature": "10", "unit": "celsius"})
    elif "san francisco" in location.lower():
        return json.dumps(
            {"location": "San Francisco", "temperature": "72", "unit": "fahrenheit"}
        )
    elif "paris" in location.lower():
        return json.dumps({"location": "Paris", "temperature": "22", "unit": "celsius"})
    else:
        return json.dumps({"location": location, "temperature": "unknown"})

def anthropic_examples():
    """Anthropic SDK examples: tools only, json mode, tools + json mode"""
    try:
        print("=== ANTHROPIC SDK EXAMPLES ===")
        client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        
        # Example 1: Tool only (tool_choice: "auto")
        print("\n--- 1. Anthropic: Tool Only (auto) ---")
        tools = [{
            "name": "get_current_weather",
            "description": "Get the current weather in a given location",
            "input_schema": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "The city and state, e.g. San Francisco, CA"
                    },
                    "unit": {
                        "type": "string",
                        "enum": ["celsius", "fahrenheit"]
                    }
                },
                "required": ["location"]
            }
        }]
        
        response = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=300,
            system="You are a weather assistant. Use tools when you need to fetch weather data.",
            messages=[
                {"role": "user", "content": "What's the weather like in San Francisco?"}
            ],
            tools=tools,
            tool_choice={"type": "auto"}  # Let model decide
        )
        
        print(f"Response: {response}")
        if response.content and any(content.type == "tool_use" for content in response.content):
            print("Model chose to use tools automatically")
        
        # Example 2: JSON mode (forced tool use for structured output)
        print("\n--- 2. Anthropic: JSON Mode (forced tool) ---")
        json_tools = [{
            "name": "format_response",
            "description": "Format the response in a structured way",
            "input_schema": {
                "type": "object",
                "properties": {
                    "answer": {"type": "string", "description": "The main answer to the question"},
                    "confidence": {"type": "number", "description": "Confidence level from 0.0 to 1.0"}
                },
                "required": ["answer", "confidence"]
            }
        }]
        
        response = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=300,
            system="You are a helpful assistant. Always use the format_response tool to structure your answers with confidence levels.",
            messages=[
                {"role": "user", "content": "What is the capital of Japan?"}
            ],
            tools=json_tools,
            tool_choice={"type": "tool", "name": "format_response"}  # Force specific tool
        )
        
        if response.content[0].type == "tool_use":
            structured_result = response.content[0].input
            print(f"Structured JSON result: {structured_result}")
        
        # Example 3: Tools + JSON mode (any tool available)
        print("\n--- 3. Anthropic: Tools + JSON Mode (any) ---")
        combined_tools = [
            {
                "name": "get_current_weather",
                "description": "Get the current weather in a given location",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "location": {
                            "type": "string",
                            "description": "The city and state, e.g. San Francisco, CA"
                        },
                        "unit": {
                            "type": "string",
                            "enum": ["celsius", "fahrenheit"]
                        }
                    },
                    "required": ["location"]
                }
            },
            {
                "name": "weather_report",
                "description": "Generate a structured weather report",
                "input_schema": WeatherReport.model_json_schema()
            }
        ]
        
        response = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=400,
            system="You are a weather assistant. Fetch weather data until you can create a complete report.",
            messages=[
                {"role": "user", "content": "Get me a weather report for Paris"}
            ],
            tools=combined_tools,
            tool_choice={"type": "any"}  # Model can choose any available tool
        )
        
        print(f"Response with multiple tools available: {response}")
        if response.content and any(content.type == "tool_use" for content in response.content):
            for content in response.content:
                if content.type == "tool_use":
                    print(f"Model chose tool: {content.name}")
                    print(f"Tool input: {content.input}")
        
    except Exception as e:
        print(f"Anthropic error: {e}")

def openai_examples():
    """OpenAI SDK examples: tools + response_format agent loop"""
    try:
        print("\n=== OPENAI SDK EXAMPLES ===")
        
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        print("\n--- OpenAI: Weather Agent Loop (loop until finish_reason=stop) ---")
        
        # Initialize conversation
        messages = [
            {"role": "system", "content": "You are a weather assistant. Use tools to get weather data, then provide a structured response."},
            {"role": "user", "content": "What's the weather like in San Francisco, Tokyo, and Paris?"}
        ]
        
        tools = [{
            "type": "function",
            "function": {
                "name": "get_current_weather",
                "description": "Get the current weather in a given location",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "location": {
                            "type": "string",
                            "description": "The city and state, e.g. San Francisco, CA"
                        },
                        "unit": {
                            "type": "string",
                            "enum": ["celsius", "fahrenheit"]
                        }
                    },
                    "required": ["location", "unit"],
                    "additionalProperties": False
                },
                "strict": True
            }
        }]
        
        # Agent loop: continue until finish_reason is "stop"
        step = 1
        while True:
            print(f"\n--- Agent Loop Step {step} ---")
            
            response = client.chat.completions.parse(
                model="gpt-4o-mini",
                messages=messages,
                tools=tools,
                tool_choice="auto",
                response_format=WeatherReport
            )
            
            print(f"Finish reason: {response.choices[0].finish_reason}")
            
            # Check if we're done
            if response.choices[0].finish_reason == "stop":
                print("Agent loop completed - final response received")
                print(f"Final response: {response.choices[0].message.content}")
                
                # Parse the structured response
                try:
                    weather_report = WeatherReport.model_validate_json(response.choices[0].message.content)
                    print(f"Parsed weather report: {weather_report}")
                except Exception as e:
                    print(f"Error parsing JSON: {e}")
                break
            
            # Handle tool calls
            if response.choices[0].finish_reason == "tool_calls":
                print("Tool calls detected - executing functions")
                
                # Add assistant's response to conversation
                messages.append(response.choices[0].message)
                
                # Execute each tool call
                for tool_call in response.choices[0].message.tool_calls:
                    function_name = tool_call.function.name
                    function_args = json.loads(tool_call.function.arguments)
                    
                    if function_name == "get_current_weather":
                        function_response = get_current_weather(
                            location=function_args.get("location"),
                            unit=function_args.get("unit", "fahrenheit")
                        )
                        print(f"Tool result for {function_args.get('location')}: {function_response}")
                        
                        # Add function response to conversation
                        messages.append({
                            "tool_call_id": tool_call.id,
                            "role": "tool",
                            "name": function_name,
                            "content": function_response
                        })
            
            step += 1
            if step > 10:  # Safety break
                print("Max steps reached - breaking loop")
                break
        
        print("Note: OpenAI supports both tools and response_format in the same call!")
        
    except Exception as e:
        print(f"OpenAI error: {e}")

def litellm_examples():
    """LiteLLM examples: unified tools across providers"""
    try:
        print("\n=== LITELLM EXAMPLES ===")
        
        print("\n--- LiteLLM: Combined Tools (Cross-Provider) ---")
        
        # Combined tools like the Anthropic example
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "get_current_weather",
                    "description": "Get the current weather in a given location",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "location": {
                                "type": "string",
                                "description": "The city and state, e.g. San Francisco, CA"
                            },
                            "unit": {
                                "type": "string",
                                "enum": ["celsius", "fahrenheit"]
                            }
                        },
                        "required": ["location"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "weather_report",
                    "description": "Generate a structured weather report",
                    "parameters": WeatherReport.model_json_schema()
                }
            }
        ]
        
        print("Demonstrating weather agent loop that terminates when 'weather_report' tool is called...")
        
        for model in ["gpt-4o-mini", "claude-3-haiku-20240307"]:
            try:
                print(f"\n--- Agent loop with [{model}] (loop until weather_report tool) ---")
                
                messages = [
                    {"role": "system", "content": "You are a weather assistant. First get weather data for locations, then generate a structured weather report."},
                    {"role": "user", "content": "What's the weather like in San Francisco and Tokyo?"}
                ]
                
                # Agent loop: continue until weather_report tool is called
                step = 1
                weather_report_called = False
                
                while True:
                    print(f"\n--- Agent Loop Step {step} ---")
                    
                    response = litellm.completion(
                        model=model,
                        messages=messages,
                        tools=tools,
                        tool_choice="required"  # Force tool use (same as Anthropic "any")
                    )
                    
                    if response.choices[0].message.tool_calls:
                        print(f"Tool calls detected")
                        
                        # Add assistant's response
                        messages.append(response.choices[0].message)
                        
                        # Execute each tool call
                        for tool_call in response.choices[0].message.tool_calls:
                            function_name = tool_call.function.name
                            function_args = json.loads(tool_call.function.arguments)
                            
                            if function_name == "get_current_weather":
                                function_response = get_current_weather(
                                    location=function_args.get("location"),
                                    unit=function_args.get("unit", "fahrenheit")
                                )
                                print(f"Weather data for {function_args.get('location')}: {function_response}")
                                
                                messages.append({
                                    "tool_call_id": tool_call.id,
                                    "role": "tool",
                                    "name": function_name,
                                    "content": function_response
                                })
                            
                            elif function_name == "weather_report":
                                print(f"Weather report tool called - agent loop complete!")
                                print(f"Report data: {function_args}")
                                
                                # Parse the weather report
                                try:
                                    weather_report = WeatherReport.model_validate(function_args)
                                    print(f"Parsed weather report: {weather_report}")
                                except Exception as e:
                                    print(f"Error parsing weather report: {e}")
                                
                                weather_report_called = True
                                break
                    
                    # Check if we should exit the main loop
                    if weather_report_called:
                        break
                    
                    step += 1
                    if step > 10:  # Safety break
                        print(f"Max steps reached - breaking loop")
                        break
                
            except Exception as e:
                print(f"Error with {model}: {e}")

    except Exception as e:
        print(f"LiteLLM error: {e}")

def main():
    """Run all provider examples"""
    print("Provider Comparison: Tool Calls vs Response Format")
    print("=" * 60)
    
    # Initialize Langfuse for tracing
    langfuse = Langfuse()
    
    anthropic_examples()
    openai_examples() 
    litellm_examples()
    
    # Flush traces to Langfuse
    langfuse.flush()

if __name__ == "__main__":
    main()
