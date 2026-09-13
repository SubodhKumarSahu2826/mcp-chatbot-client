import subprocess
import os
import shutil

from mcp.server.fastmcp import FastMCP


mcp = FastMCP("Manim Server")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MEDIA_DIR = os.path.join(BASE_DIR, "media")

os.makedirs(MEDIA_DIR, exist_ok=True)


@mcp.tool()
def execute_manim_code(manim_code: str) -> str:
    """Execute Manim code and return the generated video path."""

    tmpdir = os.path.join(MEDIA_DIR, "manim_tmp")
    os.makedirs(tmpdir, exist_ok=True)

    script_path = os.path.join(tmpdir, "scene.py")

    try:
        with open(script_path, "w", encoding="utf-8") as f:
            f.write(manim_code)

        result = subprocess.run(
            [
                "manim",
                "-ql",
                "--media_dir",
                MEDIA_DIR,
                script_path
            ],
            capture_output=True,
            text=True,
            cwd=tmpdir
        )

        if result.returncode != 0:
            return f"Execution failed:\n{result.stderr}"

        # Find generated MP4
        for root, _, files in os.walk(MEDIA_DIR):
            for file in files:
                if file.endswith(".mp4"):
                    return os.path.join(root, file)

        return "Manim completed, but no video file was found."

    except Exception as e:
        return f"Error during execution: {e}"


@mcp.tool()
def cleanup_manim_temp_dir(directory: str) -> str:
    """Clean up the specified Manim temporary directory."""

    try:
        if os.path.exists(directory):
            shutil.rmtree(directory)
            return f"Cleanup successful for directory: {directory}"

        return f"Directory not found: {directory}"

    except Exception as e:
        return f"Cleanup failed: {e}"


if __name__ == "__main__":
    mcp.run(transport="stdio")