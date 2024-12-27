from git_mirror.main import entrypoint
from loguru import logger as log

def main():
    try:
        entrypoint(add_file_logger=True, add_error_file_logger=True, colorize=True)
        
        log.success("Script completed without raising an exception. Git errors may have occurred, you should review the logs.")
    except Exception as exc:
        msg = f"({type(exc)}) Error running git-mirror package. Details: {exc}"
        print(f"[ERROR] {msg}")
        
        exit(1)

if __name__ == "__main__":
    main()