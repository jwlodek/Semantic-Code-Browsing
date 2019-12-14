#!/usr/bin/env python3

import argparse
import os
import code_browsing.program_parser as PARSER
import code_browsing.query_engine as QUERY_ENGINE





def main():
    parser = argparse.ArgumentParser(description='A python utility for sematically browsing python and prolog code.')
    parser.add_argument('programpath', help='Enter the path to the program or directory you wish to browse.')
    args = vars(parser.parse_args())
    if not os.path.exists(args['programpath']):
        print('ERROR - Path {} does not exist!'.format(args['programpath']))
    else:
        parser = PARSER.PrologProgramParser()
        parser.parse_program(args['programpath'])
        parser.program_representation.print_representation()


if __name__ == "__main__":
    main()