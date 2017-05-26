import agent.agent as agent
import sys
from ioant.utils import utils
import os


def init_ascii():
    message = "\
=========================================================================\n\
|                       Agent Entity                                    |\n\
========================================================================="
    return message

relative_path_steps = "../../../../../"

if __name__ == "__main__":
    print(init_ascii())
    logging.info('Starting entity agent')
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
