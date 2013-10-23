# -*- coding: utf-8 -*-
from plone.recipe.codeanalysis.utils import _normalize_boolean
from plone.recipe.codeanalysis.utils import _read_subprocess_output
from utils import _process_output
from plone.recipe.codeanalysis.utils import log

import os
import re
from tempfile import TemporaryFile


def csslint_errors(output, jenkins=False):
    """Search for error markers as CSS Lint always return an exit code of 0
    either if a file has errors or just warnings.
    """
    pattern = r'severity="error"' if jenkins else r'Error -'
    error = re.compile(pattern)
    return error.search(output)


def code_analysis_csslint(options):
    log('title', 'CSS Lint')
    jenkins = _normalize_boolean(options['jenkins'])

    # cmd is a sequence of program arguments
    # first argument is child program
    paths = options['directory'].split('\n')
    cmd = [options['csslint-bin']] + paths

    try:
        if jenkins:
            cmd.insert(1, '--format=lint-xml')
            # Get only errors, no warnings.
            cmd.insert(2, '--errors=important')
            output_file_name = os.path.join(options['location'], 'csslint.xml')
            output_file = open(output_file_name, 'w+')
        else:
            cmd.insert(1, '--format=compact')
            # Get only errors, no warnings.
            cmd.insert(2, '--errors=important')
            cmd.insert(3, '--quiet')  # Only output when error found.
            output_file = TemporaryFile('w+')

        # Wrapper to subprocess.Popen
        try:
            # Return code is not used for csslint.
            output = _read_subprocess_output(cmd, output_file)[0]
        except OSError:
            log('skip')
            return False
    finally:
        output_file.close()

    if csslint_errors(output, jenkins):
        log('failure')
        # TODO: pass color to _process_output
        # Name the pattern to use it in the substitution.
        old, new = '(?P<name>Error[^ -]*)', '\033[00;31m\g<name>\033[0m'
        print _process_output(output, old, new)
        return False
    else:
        log('ok')
        return True
