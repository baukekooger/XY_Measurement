import logging

loggerchild = logging.getLogger('parentlogger.child')
loggerchild.info('this is the child speaking')


class Foo:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.logger.debug('Init Foo')


if __name__ == '__main__':
    import yaml
    import logging.config
    with open('logconfig.yaml', 'r') as f:
        config = yaml.safe_load(f.read())
        logging.config.dictConfig(config)

