import sys
import json
import subprocess

def run_imagemagick(params):
    """Executes an ImageMagick command and returns the result."""
    command = ['convert'] + params.get('args', [])
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        return {
            "success": True,
            "stdout": result.stdout,
            "stderr": result.stderr
        }
    except subprocess.CalledProcessError as e:
        return {
            "success": False,
            "error": "ImageMagick command failed",
            "stdout": e.stdout,
            "stderr": e.stderr,
            "returncode": e.returncode
        }
    except FileNotFoundError:
        return {"success": False, "error": "ImageMagick 'convert' command not found."}

def main():
    """Main loop to handle MCP requests."""
    for line in sys.stdin:
        try:
            request = json.loads(line)
            tool = request.get('tool')
            params = request.get('params', {})

            response = {}
            if tool == 'process_image':
                response['result'] = run_imagemagick(params)
            else:
                response['error'] = f"Unknown tool: {tool}"

            sys.stdout.write(json.dumps(response) + '\n')
            sys.stdout.flush()
        except json.JSONDecodeError:
            error_response = {"error": "Invalid JSON received"}
            sys.stdout.write(json.dumps(error_response) + '\n')
            sys.stdout.flush()

if __name__ == "__main__":
    main()