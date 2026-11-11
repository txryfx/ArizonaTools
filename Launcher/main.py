import subprocess
import sys

if __name__ == "__main__":
    projects = ['arizona', 'rodina'] if '--all' in sys.argv else [sys.argv[1]] if len(sys.argv) == 2 and sys.argv[1] in {'arizona', 'rodina'} else None
    if projects is None:
        raise RuntimeError("[INFO] 👉 Usage: python main.py <arizona|rodina|--all>")

    for project in projects:
        print(f"\n{'='*50}")
        print(f"[INFO] ⚡ STARTING BUILD FOR: {project}")
        print(f"{'='*50}\n")
        subprocess.run(["python", "build_launcher.py", project], check=True)