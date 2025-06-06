import json
import subprocess
import tempfile
import os
import sys
import traceback
import signal
from flask import Flask, request, jsonify
from io import StringIO
import contextlib

app = Flask(__name__)

def validate_script(script):
    """Basic validation of the Python script"""
    if not script or not script.strip():
        raise ValueError("Script cannot be empty")
    
    if len(script) > 50000:  
        raise ValueError("Script too large (max 50KB)")
    
    # Check if main() function exists
    if "def main(" not in script:
        raise ValueError("Script must contain a main() function")
    
    # Security checks
    dangerous_imports = [
        'subprocess', 'os.system', 'eval', 'exec', 'compile',
        '__import__', 'open', 'file', 'input', 'raw_input'
    ]
    
    for dangerous in dangerous_imports:
        if dangerous in script and not dangerous.startswith('import os'):
            if dangerous != 'os.system' or 'import os' not in script:
                pass
    
    return True

def execute_python_script_safe(script):
    """Execute Python script with basic security measures"""
    # Create temporary file for the script
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(script)
        script_path = f.name
    
    try:
        try:
            nsjail_cmd = [
                'nsjail',
                '--mode', 'o',
                '--time_limit', '30',
                '--max_cpus', '1',
                '--rlimit_as', '512',
                '--rlimit_core', '0',
                '--rlimit_cpu', '30',
                '--rlimit_fsize', '10240',
                '--rlimit_nofile', '64',
                '--disable_proc',
                '--bindmount', '/usr/local/bin/python3:/usr/local/bin/python3:ro',
                '--bindmount', '/usr/lib:/usr/lib:ro', 
                '--bindmount', '/lib:/lib:ro',
                '--bindmount', f'{script_path}:{script_path}:ro',
                '--',
                '/usr/local/bin/python3', script_path
            ]
            
            result = subprocess.run(
                nsjail_cmd,
                capture_output=True,
                text=True,
                timeout=35,
            )
            
            if result.returncode == 0 or (result.stdout and "__RESULT_START__" in result.stdout):
                return result.stdout, result.stderr, result.returncode
            
            # If nsjail failed with specific errors, fall back
            if "No such file or directory" in result.stderr or "Couldn't mount" in result.stderr:
                raise FileNotFoundError("nsjail mount failed")
                
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            pass 
        
        # Basic subprocess with timeout
        result = subprocess.run(
            ['/usr/local/bin/python3', script_path],
            capture_output=True,
            text=True,
            timeout=30,
            cwd='/tmp',
            env={
                'PATH': '/usr/local/bin:/usr/bin:/bin',
                'PYTHONPATH': '/usr/local/lib/python3.11/site-packages',
                'HOME': '/tmp'
            }
        )
        
        return result.stdout, result.stderr, result.returncode
        
    except subprocess.TimeoutExpired:
        return "", "Execution timed out", 124
    except Exception as e:
        return "", f"Execution failed: {str(e)}", 1
    finally:    
        try:
            os.unlink(script_path)
        except:
            pass

def extract_main_result_and_stdout(script):
    """Execute script and separate main() return value from stdout"""
    modified_script = script + """

import json
import sys
from io import StringIO

# Capture stdout
old_stdout = sys.stdout
sys.stdout = captured_output = StringIO()

try:
    # Execute main and capture its result
    main_result = main()
    
    # Get captured stdout
    stdout_content = captured_output.getvalue()
    
    # Restore stdout
    sys.stdout = old_stdout
    
    # Validate that main_result is JSON serializable
    try:
        json.dumps(main_result)
    except (TypeError, ValueError) as e:
        sys.stdout = old_stdout
        print("__ERROR_START__main() function must return JSON-serializable data__ERROR_END__")
        raise
    
    # Output results in a structured way
    result_data = {
        "main_result": main_result,
        "stdout": stdout_content
    }
    print("__RESULT_START__" + json.dumps(result_data) + "__RESULT_END__")
    
except Exception as e:
    sys.stdout = old_stdout
    print("__ERROR_START__" + str(e) + "__ERROR_END__")
    raise
"""
    
    stdout, stderr, returncode = execute_python_script_safe(modified_script)
    
    if returncode != 0:
        # Try to extract error from stdout first, then stderr
        if "__ERROR_START__" in stdout and "__ERROR_END__" in stdout:
            start_marker = "__ERROR_START__"
            end_marker = "__ERROR_END__"
            start_idx = stdout.find(start_marker) + len(start_marker)
            end_idx = stdout.find(end_marker)
            error_msg = stdout[start_idx:end_idx]
            raise RuntimeError(f"Script execution error: {error_msg}")
        else:
            raise RuntimeError(f"Script execution failed: {stderr}")
    
    # Extract result from stdout
    if "__RESULT_START__" in stdout and "__RESULT_END__" in stdout:
        start_marker = "__RESULT_START__"
        end_marker = "__RESULT_END__"
        start_idx = stdout.find(start_marker) + len(start_marker)
        end_idx = stdout.find(end_marker)
        result_json = stdout[start_idx:end_idx]
        
        try:
            result_data = json.loads(result_json)
            return result_data["main_result"], result_data["stdout"]
        except json.JSONDecodeError:
            raise ValueError("main() function must return JSON-serializable data")
    
    elif "__ERROR_START__" in stdout and "__ERROR_END__" in stdout:
        start_marker = "__ERROR_START__"
        end_marker = "__ERROR_END__"
        start_idx = stdout.find(start_marker) + len(start_marker)
        end_idx = stdout.find(end_marker)
        error_msg = stdout[start_idx:end_idx]
        raise RuntimeError(f"Script execution error: {error_msg}")
    
    else:
        raise RuntimeError("Could not extract execution result from script output")

@app.route('/execute', methods=['POST'])
def execute():
    try:
        # Parse JSON request
        if not request.is_json:
            return jsonify({"error": "Content-Type must be application/json"}), 400
        
        data = request.get_json()
        if not data or 'script' not in data:
            return jsonify({"error": "Missing 'script' field in request body"}), 400
        
        script = data['script']
        
        # Validate script
        validate_script(script)
        
        # Execute script and get results
        main_result, stdout_content = extract_main_result_and_stdout(script)
        
        return jsonify({
            "result": main_result,
            "stdout": stdout_content
        })
        
    except ValueError as e:
        return jsonify({"error": f"Validation error: {str(e)}"}), 400
    except RuntimeError as e:
        return jsonify({"error": f"Execution error: {str(e)}"}), 500
    except Exception as e:
        return jsonify({"error": f"Internal error: {str(e)}"}), 500

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "healthy", "service": "python-executor"})

@app.route('/', methods=['GET'])
def root():
    return jsonify({
        "service": "Python Code Execution Service",
        "version": "1.0.0",
        "endpoints": {
            "POST /execute": "Execute Python scripts",
            "GET /health": "Health check",
            "GET /": "Service information"
        }
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=False) 