import os
import time


def main() -> None:
    redis_url = os.getenv("REDIS_URL", "redis://redis:6379/0")
    while True:
        print(f"Polling deployment queue on {redis_url}")
        time.sleep(15)


if __name__ == "__main__":
    main()

