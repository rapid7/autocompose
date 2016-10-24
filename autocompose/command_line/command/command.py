class Command(object):
    def __init__(self, argument_parser, function):
        self.argument_parser = argument_parser
        self.function = function

    def parse_and_execute(self, args, aws_session, docker_client):
        arguments = self.argument_parser.parse_args(args)
        self.function(aws_session=aws_session, docker_client=docker_client, **vars(arguments))
        pass
