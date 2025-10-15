#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "fastapi==0.115.12",
#     "uvicorn==0.34.0",
# ]
# ///

"""
Exercise 1: Basic API Server
A simple API with mathematical operations to understand hosting concepts
"""

from fastapi import FastAPI, HTTPException
from typing import Dict, Any

app = FastAPI(
    title="Simple Math API",
    description="A basic API server for learning hosting concepts"
)


@app.get("/")
def root() -> Dict[str, Any]:
    """Welcome endpoint with API documentation"""
    return {
        "message": "Welcome to the Simple Math API!",
        "endpoints": {
            "/hello": "GET - Returns a greeting",
            "/sum": "GET - Add two numbers (params: a, b)",
            "/subtract": "GET - Subtract b from a (params: a, b)",
            "/multiply": "GET - Multiply two numbers (params: a, b)",
            "/divide": "GET - Divide a by b (params: a, b)",
        },
        "example": "Try: curl http://localhost:8000/sum?a=5&b=3"
    }


@app.get("/hello")
def hello(name: str = "World") -> Dict[str, str]:
    """
    Simple greeting endpoint

    Example: curl "http://localhost:8000/hello?name=Alice"
    """
    return {
        "message": f"Hello, {name}!",
        "endpoint": "/hello"
    }


@app.get("/sum")
def add_numbers(a: float, b: float) -> Dict[str, Any]:
    """
    Add two numbers

    Example: curl "http://localhost:8000/sum?a=5&b=3"
    """
    result = a + b
    return {
        "operation": "sum",
        "a": a,
        "b": b,
        "result": result
    }


@app.get("/subtract")
def subtract_numbers(a: float, b: float) -> Dict[str, Any]:
    """
    Subtract b from a

    Example: curl "http://localhost:8000/subtract?a=10&b=3"
    """
    result = a - b
    return {
        "operation": "subtract",
        "a": a,
        "b": b,
        "result": result
    }


@app.get("/multiply")
def multiply_numbers(a: float, b: float) -> Dict[str, Any]:
    """
    Multiply two numbers

    Example: curl "http://localhost:8000/multiply?a=4&b=5"
    """
    result = a * b
    return {
        "operation": "multiply",
        "a": a,
        "b": b,
        "result": result
    }


@app.get("/divide")
def divide_numbers(a: float, b: float) -> Dict[str, Any]:
    """
    Divide a by b

    Example: curl "http://localhost:8000/divide?a=10&b=2"
    """
    if b == 0:
        raise HTTPException(
            status_code=400,
            detail="Cannot divide by zero!"
        )

    result = a / b
    return {
        "operation": "divide",
        "a": a,
        "b": b,
        "result": result
    }


if __name__ == "__main__":
    import uvicorn
    print("\n" + "="*50)
    print("Starting Simple Math API Server")
    print("="*50)
    print("\nServer running on: http://localhost:8000")
    print("API docs at: http://localhost:8000/docs")
    print("\nTry these commands in another terminal:")
    print("   curl http://localhost:8000/")
    print('   curl "http://localhost:8000/sum?a=5&b=3"')
    print('   curl "http://localhost:8000/hello?name=YourName"')
    print("\nPress CTRL+C to stop the server\n")
    print("="*50 + "\n")

    uvicorn.run(app, host="0.0.0.0", port=8000)
