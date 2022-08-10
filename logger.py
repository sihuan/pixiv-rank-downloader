from loguru import logger
import sys

logger.remove()
logger.add(sys.stderr, level="TRACE")
# logger.add('log/updatedb.log', level="INFO")
# logger.add('log/debug/{time}.log', level="DEBUG",retention=2,rotation='5 MB')