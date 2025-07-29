import sys
import json
import subprocess
import os
from pathlib import Path

def run_pbr_generator(params):
    """Executes the PBR generator command and returns the result."""

    # Base command
    command = [
        "/opt/venv312/bin/python",
        "/opt/tessellating-pbr-generator/main.py"
    ]

    # Add arguments from params
    material = params.get('material')
    if not material:
        return {"success": False, "error": "Missing required parameter: material"}

    command.extend(["--material", material])

    # Output directory
    output_dir = params.get('output', '/workspace/pbr_outputs')
    command.extend(["--output", output_dir])

    # Optional arguments
    if 'config' in params:
        command.extend(["--config", params['config']])
    if 'resolution' in params:
        command.extend(["--resolution", params['resolution']])
    if 'types' in params:
        command.extend(["--types"] + params['types'])
    if params.get('preview'):
        command.append("--preview")
    if params.get('debug'):
        command.append("--debug")

    try:
        # Ensure output directory exists
        Path(output_dir).mkdir(parents=True, exist_ok=True)

        # Execute the command
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=True,
            env=os.environ
        )

        # Find generated files
        generated_files = [str(f) for f in Path(output_dir).glob(f"{material}_*")]

        return {
            "success": True,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "generated_files": generated_files
        }

    except subprocess.CalledProcessError as e:
        return {
            "success": False,
            "error": "PBR generator command failed",
            "stdout": e.stdout,
            "stderr": e.stderr,
            "returncode": e.returncode
        }
    except FileNotFoundError:
        return {"success": False, "error": "PBR generator 'main.py' not found."}

def main():
    """Main loop to handle MCP requests."""
    for line in sys.stdin:
        try:
            request = json.loads(line)
            tool = request.get('tool')
            params = request.get('params', {})

            response = {}
            if tool == 'generate_material':
                response['result'] = run_pbr_generator(params)
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