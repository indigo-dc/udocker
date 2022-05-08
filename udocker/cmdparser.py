# -*- coding: utf-8 -*-
"""Parser for udocker commands and options"""

import string


class CmdParser(object):
    """Implements a simple command line parser.
    Divides the command into parameters and options
    that can be queried for presence and value.
    The general command format is:
      $ udocker command arg1 arg2 --opta --optb=zzz
    """

    def __init__(self):
        """constructor parses the user command line"""
        self._argv = ""
        self._argv_split = {}
        self._argv_consumed_options = {}
        self._argv_consumed_params = {}
        self._argv_split['CMD'] = ""
        self._argv_split['GEN_OPT'] = []
        self._argv_split['CMD_OPT'] = []
        self._argv_consumed_options['GEN_OPT'] = []
        self._argv_consumed_options['CMD_OPT'] = []
        self._argv_consumed_params['GEN_OPT'] = []
        self._argv_consumed_params['CMD_OPT'] = []

    def parse(self, argv):
        """Parse a command line string.
        Divides the string in three blocks: general_options,
        command name, and command options+arguments
        """
        step = 1
        for arg in argv[1:]:
            if not arg:
                continue

            if step == 1:
                if arg[0] in string.ascii_letters:
                    self._argv_split['CMD'] = arg
                    step = 2
                else:
                    self._argv_split['GEN_OPT'].append(arg)
            elif step == 2:
                self._argv_split['CMD_OPT'].append(arg)

        return step == 2

    def missing_options(self):
        """Get command line options not used/fetched by Cmdp.get()
        """
        all_opt = []
        for pos in range(len(self._argv_split['GEN_OPT'])):
            if (pos not in self._argv_consumed_options['GEN_OPT'] and
                    pos not in self._argv_consumed_params['GEN_OPT']):
                all_opt.append(self._argv_split['GEN_OPT'][pos])

        for pos in range(len(self._argv_split['CMD_OPT'])):
            if (pos not in self._argv_consumed_options['CMD_OPT'] and
                    pos not in self._argv_consumed_params['CMD_OPT']):
                all_opt.append(self._argv_split['CMD_OPT'][pos])

        return all_opt

    def get(self, opt_name, opt_where="CMD_OPT", opt_multiple=False):
        """Get the value of a command line option --xyz=
        multiple=true  multiple occurences of option can be present
        """
        if opt_where == "CMD":
            return self._argv_split["CMD"]

        if opt_where in ("CMD_OPT", "GEN_OPT"):
            if opt_name.startswith('P'):
                return (self._get_param(opt_name,
                                        self._argv_split[opt_where],
                                        self._argv_consumed_options[opt_where],
                                        self._argv_consumed_params[opt_where]))

            if opt_name.startswith('-'):
                return (self._get_option(opt_name,
                                         self._argv_split[opt_where],
                                         self._argv_consumed_options[opt_where],
                                         opt_multiple))

        return None

    def declare_options(self, opts_string, opt_where="CMD_OPT"):
        """Declare in advance options that are part of the command line
        """
        pos = 0
        opt_list = self._argv_split[opt_where]
        while pos < len(opt_list):
            for opt_name in opts_string.strip().split():
                if opt_name.endswith('='):
                    if opt_list[pos].startswith(opt_name):
                        self._argv_consumed_options[opt_where].append(pos)
                    elif opt_list[pos] == opt_name[:-1]:
                        self._argv_consumed_options[opt_where].append(pos)
                        if pos + 1 == len(opt_list):
                            break   # error -x without argument at end of line
                        if (pos < len(opt_list) and
                                not opt_list[pos+1].startswith('-')):
                            self._argv_consumed_options[opt_where].\
                                append(pos + 1)
                elif opt_list[pos] == opt_name:
                    self._argv_consumed_options[opt_where].append(pos)
            pos += 1

    def _get_option(self, opt_name, opt_list, consumed, opt_multiple):
        """Get command line options such as: -x -x= --x --x=
        The options may exist in the first and third part of the udocker
        command line.
        """
        all_args = []
        pos = 0
        list_len = len(opt_list)
        while pos < list_len:
            opt_arg = None
            if ((not opt_list[pos].startswith('-')) and
                    (pos < 1 or (pos not in consumed and not
                                 opt_list[pos-1].endswith('=')))):
                break        # end of options and start of arguments

            if opt_name.endswith('='):
                if opt_list[pos].startswith(opt_name):
                    opt_arg = opt_list[pos].split('=', 1)[1].strip()
                elif (opt_list[pos] == opt_name[:-1] and
                      pos + 1 == list_len):
                    break    # error --arg at end of line
                elif (opt_list[pos] == opt_name[:-1] and
                      not opt_list[pos + 1].startswith('-')):
                    consumed.append(pos)
                    pos += 1
                    opt_arg = opt_list[pos]
            elif opt_list[pos] == opt_name:
                consumed.append(pos)
                opt_arg = True

            pos += 1
            if opt_arg is None:
                continue

            consumed.append(pos-1)
            if opt_multiple:
                all_args.append(opt_arg)
            else:
                return opt_arg

        if opt_multiple:
            return all_args

        return False

    def _get_param(self, opt_name, opt_list, consumed, consumed_params):
        """Get command line parameters
        The CLI of udocker has 3 parts, first options, second command name
        third everything after the command name. The params are the arguments
        that do not start with - and may exist after the options.
        """
        all_args = []
        pos = 0
        param_num = 0
        skip_opts = True
        while pos < len(opt_list):
            if opt_list[pos] == "-":
                skip_opts = False

            if not (skip_opts and
                    (opt_list[pos].startswith('-') or pos in consumed)):
                skip_opts = False
                param_num += 1
                if opt_name[1:] == str(param_num):
                    consumed_params.append(pos)
                    return opt_list[pos]

                if opt_name[1] == '*':
                    consumed_params.append(pos)
                    all_args.append(opt_list[pos])
                elif opt_name[1] == '+' and param_num > 0:
                    consumed_params.append(pos)
                    all_args.append(opt_list[pos])
            pos += 1

        if opt_name[1] == '*':
            return all_args

        if opt_name[1] == '+':
            return all_args[1:]

        return None
