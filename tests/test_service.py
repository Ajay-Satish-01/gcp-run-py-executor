#!/usr/bin/env python3
"""
Test script for the Python Code Execution Service
"""

import requests
import json
import time

def test_basic_execution():
    """Test basic script execution"""
    url = "http://localhost:8080/execute"
    script = '''
def main():
    return {"message": "Hello World!", "number": 42}
'''
    
    response = requests.post(url, json={"script": script})
    print("Basic execution test:")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    print()

def test_with_stdout():
    """Test script with stdout capture"""
    url = "http://localhost:8080/execute"
    script = '''
def main():
    print("This is stdout output")
    print("Another line")
    return {"result": "success", "data": [1, 2, 3]}
'''
    
    response = requests.post(url, json={"script": script})
    print("Stdout capture test:")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    print()

def test_pandas_numpy():
    """Test with pandas and numpy"""
    url = "http://localhost:8080/execute"
    script = '''
def main():
    import pandas as pd
    import numpy as np
    
    # Create sample data
    data = pd.DataFrame({"values": [1, 2, 3, 4, 5]})
    mean_val = data["values"].mean()
    
    print(f"Processing {len(data)} rows of data")
    
    return {
        "mean": mean_val,
        "count": len(data),
        "numpy_version": np.__version__,
        "pandas_version": pd.__version__
    }
'''
    
    response = requests.post(url, json={"script": script})
    print("Pandas/Numpy test:")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    print()

def test_error_handling():
    """Test error handling"""
    url = "http://localhost:8080/execute"
    
    # Test missing main function
    script_no_main = "print('Hello')"
    response = requests.post(url, json={"script": script_no_main})
    print("Error handling test (no main function):")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    print()
    
    # Test runtime error
    script_error = '''
def main():
    raise ValueError("Test error")
'''
    response = requests.post(url, json={"script": script_error})
    print("Error handling test (runtime error):")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    print()

def test_health_endpoint():
    """Test health endpoint"""
    url = "http://localhost:8080/health"
    response = requests.get(url)
    print("Health endpoint test:")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    print()

if __name__ == "__main__":
    print("Testing Python Code Execution Service...")
    print("Make sure the service is running on localhost:8080")
    print("=" * 50)
    
    try:
        test_health_endpoint()
        test_basic_execution()
        test_with_stdout()
        test_pandas_numpy()
        test_error_handling()
        print("All tests completed!")
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to service. Make sure it's running on localhost:8080")
    except Exception as e:
        print(f"Error running tests: {e}") 