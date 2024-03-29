#!/usr/bin/env python3

import argparse
import os
import code_browsing.query_engine as QUERY_ENGINE



def main():
    parser = argparse.ArgumentParser(description='A python utility for sematically browsing python and prolog code.')
    parser.add_argument('programpath', help='Enter the path to the program or directory you wish to browse.')
    args = vars(parser.parse_args())
    query_shell = QUERY_ENGINE.QueryShell(args['programpath'])
    query_shell.run_shell()


if __name__ == "__main__":
    main()