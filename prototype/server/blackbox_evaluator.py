import subprocess


class BlackboxEvaluator(object):
    def evaluate(self, variables_metadata, variables):
        raise NotImplementedError()


class BlackboxBinaryFileEvaluator(BlackboxEvaluator):
    def __init__(self, binary_path):
        super().__init__()
        self.binary_path = binary_path

    def evaluate(self, variables_metadata, variables):
        args = [self.binary_path]
        env_vars = dict()
        # First pass parses positional arguments
        for i, variable_metadata in enumerate(variables_metadata):
            if variable_metadata.HasField('argument_input'):
                if not variable_metadata.argument_input.arg_name:
                    args.append(str(variables[i]))
        # Second pass parses flags
        for i, variable_metadata in enumerate(variables_metadata):
            if variable_metadata.HasField('argument_input'):
                if variable_metadata.argument_input.arg_name:
                    arg_name = variable_metadata.argument_input.arg_name
                    if variable_metadata.argument_input.long_arg:
                        args.append('--' + arg_name)
                    else:
                        args.append('-' + arg_name)
                    args.append(str(variables[i]))
        # Third pass parses env variables
        for i, variable_metadata in enumerate(variables_metadata):
            if variable_metadata.HasField('environment_input'):
                env_vars[variable_metadata.environment_input.env_name] = str(
                    variables[i]
                )
        # Forth pass parses direct input
        direct_input = ''
        for i, variable_metadata in enumerate(variables_metadata):
            if variable_metadata.HasField('direct_input'):
                direct_input += str(variables[i]) + '\n'
        p = subprocess.run(
            args,
            env=env_vars,
            stdout=subprocess.PIPE,
            input=direct_input,
            encoding='ascii',
            check=True
        )
        return float(p.stdout.strip())
