import yaml
import logging.config
import logging.handlers
import unicodedata

mu = unicodedata.lookup('greek small letter mu')


with open('loggingconfig.yml') as f:
    config = yaml.safe_load(f)
    logging.config.dictConfig(config)

logger = logging.getLogger('statemachine')

logger.info(f'small greek letter {mu}')
