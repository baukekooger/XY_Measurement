import sub1
import sub2
import logging


class MainFoo:
    def __init__(self):
        self.logger = logging.getLogger('parentlogger.child')
        self.logger.info('Init Main')


if __name__ == '__main__':
    import yaml
    import logging.config
    with open('logconfig.yaml', 'r') as f:
        config = yaml.safe_load(f.read())
        logging.config.dictConfig(config)

    testmain = MainFoo()
    testfoo = sub1.Foo()
    testbar = sub2.Bar()
