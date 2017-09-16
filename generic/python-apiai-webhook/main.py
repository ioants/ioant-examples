import device.application as app
import sys
import ioant.utils as utils
import os
import logging

logging.basicConfig(filename='logs/output.log',
                    level=logging.INFO,
                    format='%(asctime)s %(name)-5s %(levelname)-8s %(message)s',
                    datefmt='%m-%d %H:%M:%S')
console = logging.StreamHandler()
logging.getLogger('').addHandler(console)


def init_ascii():
    message = "\
=========================================================================\n\
|                      Webhook - communication                          |\n\
========================================================================="
    return message


if __name__ == "__main__":
    print(init_ascii())
    logging.info('Starting webhook basic')
    script_dir = os.path.dirname(os.path.realpath(__file__))
    argument_list = sys.argv
    number_of_arguments = len(sys.argv)
    script_dir = os.path.dirname(os.path.realpath(__file__))
    if number_of_arguments is not 1:
        configuration_path = utils.return_absolut_path(os.path.dirname(__file__),
                                                       argument_list[1])
    else:
        configuration_path = utils.return_absolut_path(os.path.dirname(__file__),
                                                       'configuration.json')

    configuration = utils.fetch_json_file_as_dict(configuration_path)
    app.setup(configuration)
    while True:
        app.loop()
    sys.exit()
