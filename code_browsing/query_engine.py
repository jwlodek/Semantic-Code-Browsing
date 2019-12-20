import os
import sys
import re
import code_browsing.program_parser as PARSER
import code_browsing.errors as SCBErrors
import code_browsing.program_representation as PR
import code_browsing.logger as LOGGER
import code_browsing

class SCBQuery:

    def __init__(self, original_str, search_type, assertion_list, assertion_relationships):
        self.original_str = original_str
        self.search_type = search_type
        self.assertion_list = assertion_list
        self.assertion_relationships = assertion_relationships


class SCBQueryResult:

    def __init__(self, original_query, true_matched_terms, partially_matched_terms):
        self.original_query = original_query
        self.true_matched_terms = true_matched_terms
        self.partially_matched_terms = partially_matched_terms

    def print_result(self, fp=sys.stdout):
        fp.write('\nQuery: {}\n\n'.format(self.original_query))
        for term in self.true_matched_terms:
            fp.write(' > ')
            term.print_term(fp, verbosity='low')
        
        fp.write('\n{} Matching result(s) found.\n'.format(len(self.true_matched_terms)))

class SCBAssertion:

    def __init__(self, assertion_operator, assertion_values):
        #VALID ASSERTION OPERATORS: inputs:, bodycontains:, returns:
        self.assertion_operator = assertion_operator
        self.assertion_values = assertion_values



class QueryEngine:

    def __init__(self, program_representation):

        self.program_representation = program_representation


    def parse_assertions(self, assertion_str):
        # Make conjunction/disjunction one character for simplicity
        assertion_list = []
        assertion_relationships = []
        simplified_assertion_string = re.sub(' and ', 'A', assertion_str)
        simplified_assertion_string = re.sub(' or ', 'O', simplified_assertion_string)

        nested_assertion_counter = 0
        current_assertion = ''
        for c in simplified_assertion_string:
            if c == '(':
                nested_assertion_counter = nested_assertion_counter + 1
            elif c == ')':
                nested_assertion_counter = nested_assertion_counter - 1
            elif nested_assertion_counter == 0 and (c == 'O' or c=='A'):
                operator = current_assertion.split(':')[0]
                values = current_assertion.split(':')[1].split(',')
                assertion_list.append(SCBAssertion(operator, values))
                current_assertion = ''
                if(c == 'O'):
                    assertion_relationships.append(['or', len(assertion_list) - 1, len(assertion_list)])
                else:
                    assertion_relationships.append(['and', len(assertion_list) - 1, len(assertion_list)])
            else:
                current_assertion = current_assertion + c
        assertion_list.append(SCBAssertion(current_assertion.split(':')[0], current_assertion.split(':')[1].split(',')))

        return assertion_list, assertion_relationships


    def convert_query(self, query_str):
        # QUERY FORMAT: find PR_TYPE where ASSERTION and (ASSERTION or ASSERTION)
        try:
            query_str_stripped = re.sub(' +', ' ', query_str.lower().strip()[:-1])
            query_parts = query_str_stripped.split(' ', 3)
            if len(query_parts) == 2:
                return SCBQuery(query_str, query_parts[1], [], [])
            query_type = query_parts[1]
            assertion_str = query_parts[3]
        except IndexError:
            raise SCBErrors.SCBInvalidQueryError
        assertion_list, assertion_relationships = self.parse_assertions(assertion_str)
        return SCBQuery(query_str, query_type, assertion_list, assertion_relationships)

    def process_query(self, scb_query):
        print('\nSearching for {} that satisfy assertions:'.format(scb_query.search_type))
        for assertion in scb_query.assertion_list:
            print(' - Assertion: {} -> {}'.format(assertion.assertion_operator, assertion.assertion_values))

        if isinstance(self.program_representation, PR.PrologProgramRepresentation):
            return self.process_prolog_query(scb_query)
        elif isinstance(self.program_representation, PR.CProgramRepresentation):
            return self.process_c_query(scb_query)


    def process_c_query(self, scb_query):
        true_matches = []
        partial_matches = []
        search_arity = -1
        if scb_query.search_type.startswith('function'):
            try:
                search_arity = scb_query.search_type.split('/')[1]
            except IndexError:
                print('No arity specified of target function or predicate.')

            for func in self.program_representation.c_functions:
                if func.arity == int(search_arity) or search_arity == -1:
                    assertion_results = []
                    for assertion in scb_query.assertion_list:
                        assertion_results.append(self.check_assertion(assertion, func))
                    check = self.combine_results_with_relationships(assertion_results, scb_query.assertion_relationships)
                    if check:
                        true_matches.append(func)
        return SCBQueryResult(scb_query.original_str, true_matches, partial_matches)


    def process_prolog_query(self, scb_query):
        true_matches = []
        partial_matches = []
        search_arity = -1
        if scb_query.search_type.startswith('predicate'):
            try:
                search_arity = scb_query.search_type.split('/')[1]
            except IndexError:
                print('No arity specified of target function or predicate.')

            for pred in self.program_representation.predicates:
                if pred.arity == int(search_arity) or search_arity == -1:
                    assertion_results = []
                    for assertion in scb_query.assertion_list:
                        assertion_results.append(self.check_assertion(assertion, pred))
                    check = self.combine_results_with_relationships(assertion_results, scb_query.assertion_relationships)
                    if check:
                        true_matches.append(pred)
        return SCBQueryResult(scb_query.original_str, true_matches,partial_matches)


    def combine_results_with_relationships(self, assertion_results, assertion_relationships):
        combined_result = []
        for relation in assertion_relationships:
            if relation[0] == 'and':
                if assertion_results[relation[1]] and assertion_results[relation[2]]:
                    combined_result.append(True)
                else:
                    combined_result.append(False)
            if relation[0] == 'or':
                if assertion_results[relation[1]] or assertion_results[relation[2]]:
                    combined_result.append(True)
                else:
                    combined_result.append(False)

        for i in range(0, len(assertion_results)):
            in_relationship = False
            for relation in assertion_relationships:
                if relation[1] == i or relation[2] == i:
                    in_relationship = True
            if not in_relationship:
                combined_result.append(assertion_results[i])

        if False in combined_result:
            return False
        return True


    def check_assertion(self, assertion, term):
        # check the input types
        assertion_result = True
        if assertion.assertion_operator == 'inputs':
            for i in range(0, len(term.set_of_terms)):
                elem = term.set_of_terms[i]
                if isinstance(elem, PR.Function) and not assertion.assertion_values[i].startswith('func/'):
                    assertion_result = False
                elif isinstance(elem, PR.Function) and not elem.arity == int(assertion.assertion_values[i].split('/')[1]):
                    assertion_result = False
                elif isinstance(elem, PR.Variable) and not elem.computed_type == assertion.assertion_values[i]:
                    assertion_result = False
        elif assertion.assertion_operator == 'bodycontains':
            if not isinstance(term, PR.Predicate) and not isinstance(term, PR.Method) and not isinstance(term, PR.Function):
                assertion_result = False
            else:
                assertion_result = False
                for sub_term in term.body:
                    for assertion_val in assertion.assertion_values:
                        if assertion_val == 'function' and isinstance(sub_term, PR.Function):
                            assertion_result = True
                        elif assertion_val == 'loop' and isinstance(sub_term, PR.Loop):
                            assertion_result = True
                        elif assertion_val == 'conditional' and isinstance(sub_term, PR.Conditional):
                            assertion = True
                        elif isinstance(sub_term, PR.Function):
                            if(self.check_assertion(assertion, sub_term)):
                                assertion_result = True
        elif assertion.assertion_operator == 'returns':
            if not isinstance(term, PR.Method):
                assertion_result = False
            elif term.return_type not in assertion.assertion_values:
                assertion_result = False
        return assertion_result

class QueryShell:

    def __init__(self, program_path):

        self.program_path = program_path
        if os.path.isfile(program_path):
            self.program_type = 'Single-File'
        else:
            self.program_type = 'Module'
        self.program_representation = None
        self.load_new_program(program_path, initial_load=True)
        self.engine = QueryEngine(self.program_representation)



    def print_query_shell_welcome_message(self):
        welcome_message = '+{}+\n'.format(64 * '-')
        welcome_message = welcome_message + '|{:<64}|\n'.format(' Semantic-Code-Browsing')
        welcome_message = welcome_message + '|{}|\n'.format(64 * '-')
        welcome_message = welcome_message + '|{:<64}|\n'.format(' SCB Query Shell {}'.format(code_browsing.__version__))
        welcome_message = welcome_message + '|{:<64}|\n'.format(' {} {} Program - {}'.format(self.representation_language, self.program_type, self.program_path))
        welcome_message = welcome_message + '|{:<64}|\n'.format(' {}'.format('Jakub Wlodek - CSE 505 Final Project'))
        welcome_message = welcome_message + '+{}+\n\n'.format(64 * '-')
        welcome_message = welcome_message + 'Welcome to the Semantic Code Browsing Query Shell. Please enter a valid query for the given program,\n'
        welcome_message = welcome_message + 'or see the documentation and/or examples for instructions on constructing valid queries.\n'
        print(welcome_message)


    def print_query_shell_help(self):
        print('\nSCB Query Shell.\n--------------------------------------')
        print('All queries in the shell should be followed by a period and then enter.\nFor help with Semantic Code Browsing (SCB) Queries, use:\n')
        print(' > help scb.')
        print('\nBasic Queries:')
        print(' > exit.\n    Exits the shell.')
        print(' > help.\n    Displays this help message.')
        print(' > shell info.\n    Displays current shell information.')
        print(' > program info.\n    Prints information on all elements collected from program.')
        print(' > load program PATH.\n    Loads a new program with the specified path.')
        print(' > describe FUNCTION/ARITY\n    Prints all information about a function or predicate.\n')


    def show_scb_help(self):
        help = "\nThe format that queries entered into the query shell take is as follows:\n"
        help = help + "* Each query begins with the find keyword.\n"
        help = help + "* This is then followed by a search type, typically function or predicate with an optional arity marker.\n"
        help = help + "* Then, optionally, assertions can be added by appending the where keyword followed by assertions of the following types.\n\nEach assertion starts with a keyword and colon, followed by certain search terms. Assertions can be glued together using or and and keywords.\n\n"
        help = help + "\t1) inputs:INPUT_1_TYPE,INPUT_2_TYPE...\n"
        help = help + "\t2) bodycontains:SEARCHTYPE (SEARCHTYPE: function, loop, conditional)\n"
        help = help + "\t3) returns:RETURN_TYPE\n\n"
        help = help + "* All queries end with a period.\n"

        help = help + "Below are some examples of valid queries on an input program:\n\n"

        help = help + "SCB Query > find function/2 where inputs:int,char* or returns:void.\n"
        help = help + "SCB Query > find predicate.\n"
        help = help + "SCB Query > find predicate where bodycontains:function and inputs:function/3,var.\n"
        help = help + "SCB Query > find function where bodycontains:loop and returns:int*.\n"

        print(help)

    def print_shell_info(self):
        print('TODO')

    def print_loaded_program_info(self):
        self.program_representation.print_representation()

    def load_new_program(self, path, initial_load=False):
        if not os.path.exists(path):
            print('ERROR - Path {} does not exist!'.format(path))
            exit()
        else:
            parser = PARSER.create_parser(path)
            parser.parse_program(path)
            self.program_representation = parser.program_representation
            if not initial_load:
                self.engine.program_representation = self.program_representation
            if isinstance(self.program_representation, PR.PrologProgramRepresentation):
                self.representation_language = 'Prolog'
            elif isinstance(self.program_representation, PR.PythonProgramRepresentation):
                self.representation_language = 'Python'
            elif isinstance(self.program_representation, PR.CProgramRepresentation):
                self.representation_language = 'C'


    def show_pred_fun_info(self, query):
        pred_arity = -1
        if '/' in query:
            pred_name = query.split(' ')[1].split('/')[0]
            pred_arity = int(query.split(' ')[1].split('/')[1][:-1])
        else:
            pred_name = query.split(' ')[1][:-1]
        counter = 0
        if isinstance(self.program_representation, PR.PrologProgramRepresentation):
            symbols = self.program_representation.predicates
        elif isinstance(self.program_representation, PR.CProgramRepresentation):
            symbols = self.program_representation.c_functions
        for pred in symbols:
            if pred.name == pred_name and (pred.arity == pred_arity or pred_arity == -1):
                pred.print_term()
                counter = counter + 1
        print('\n{} Matching result(s) found.'.format(counter))

    def exit_shell(self):
        print('Exiting...')


    def run_shell(self):
        self.print_query_shell_welcome_message()
        try:
            query = None
            while query != 'exit.':
                query = input('SCB Query > ')
                while not query.endswith('.'):
                    query = query + ' ' + input('> ')
                try:
                    if query == 'exit.':
                        pass
                    elif query == 'help.':
                        self.print_query_shell_help()
                    elif query == 'shell info.':
                        self.print_shell_info()
                    elif query == 'program info.':
                        self.print_loaded_program_info()
                    elif query.startswith('load program'):
                        self.load_new_program(query.split(' ')[2][:-1])
                    elif query.startswith('describe'):
                        self.show_pred_fun_info(query)
                    elif query == 'help scb.':
                        self.show_scb_help()
                    else:
                        scb_query = self.engine.convert_query(query)
                        scb_result = self.engine.process_query(scb_query)
                        scb_result.print_result()
                except SCBErrors.SCBInvalidQueryError:
                    print('Syntax Error - The entered query was not parsable!')
            self.exit_shell()
        except KeyboardInterrupt:
            self.exit_shell()

