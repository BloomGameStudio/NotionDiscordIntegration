import logging
import sys

logging.basicConfig(
    stream=sys.stdout,
    format="[%(asctime)s] [%(filename)s:%(lineno)d] %(levelname)s - %(message)s",
    level=logging.INFO,
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger()

if __name__ == "__main__":
    logger.debug("Logging")
