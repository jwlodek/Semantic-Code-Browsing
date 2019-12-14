import os
import sys
import re
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

    def __init__(self, true_matched_terms, partially_matched_terms):
        self.true_matched_terms = true_matched_terms
        self.partially_matched_terms = partially_matched_terms

    def print_result(self, fp=sys.stdout):
        fp.write('Terms fully matched with query:\n--------------------------------------------\n')
        for term in self.true_matched_terms:
            term.print_term(fp)
        fp.write('\nTerms artially matched with query:\n----------------------------------------\n')
        for term in self.partially_matched_terms:
            term.print_term(fp)

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
        simplified_assertion_string = re.sub('and', 'A', assertion_str)
        simplified_assertion_string = re.sub('or', 'O', simplified_assertion_string)
        simplified_assertion_string = re.sub(' ', '', simplified_assertion_string)

        nested_assertion_counter = 0
        current_assertion = ''
        print(simplified_assertion_string)
        for c in simplified_assertion_string:
            if c == '(':
                nested_assertion_counter = nested_assertion_counter + 1
            elif c == ')':
                nested_assertion_counter = nested_assertion_counter - 1
            elif nested_assertion_counter == 0 and (c == 'O' or c=='A'):
                print(current_assertion)
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
        for assertion in scb_query.assertion_list:
            print(' - Assertion: {} -> {}'.format(assertion.assertion_operator, assertion.assertion_values))
        for assertion_relation in scb_query.assertion_relationships:
            print(assertion_relation)

        if isinstance(self.program_representation, PR.PrologProgramRepresentation):
            return self.process_prolog_query(scb_query)
        elif isinstance(self.program_representation, PR.CProgramRepresentation):
            return self.process_c_query(scb_query)

    def process_c_query(self):
        #TODO
        pass

    def process_prolog_query(self, scb_query):
        true_matches = []
        partial_matches = []
        if scb_query.search_type.startswith('predicate'):
            try:
                search_arity = scb_query.search_type.split('/')[1]
            except IndexError:
                print('ERROR - Please specify arity of target function or predicate.')
                return None

            for pred in self.program_representation.predicates:
                if pred.arity == int(search_arity):
                    assertion_results = []
                    for assertion in scb_query.assertion_list:
                        assertion_results.append(self.check_assertion(assertion, pred))
                    check = self.combine_results_with_relationships(assertion_results, scb_query.assertion_relationships)
                    if check:
                        true_matches.append(pred)
        return SCBQueryResult(true_matches,partial_matches)


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
            pass
        elif assertion.assertion_operator == 'returns':
            pass
        return assertion_result

class QueryShell:

    def __init__(self, program_path, program_representation):

        self.program_path = program_path
        if os.path.isfile(program_path):
            self.program_type = 'Single-File'
        else:
            self.program_type = 'Module'
        self.program_representation = program_representation
        self.engine = QueryEngine(program_representation)
        if isinstance(program_representation, PR.PrologProgramRepresentation):
            self.representation_language = 'Prolog'
        elif isinstance(program_representation, PR.PythonProgramRepresentation):
            self.representation_language = 'Python'


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
        print('TODO')

    def print_shell_info(self):
        print('TODO')

    def print_loaded_program_info(self):
        self.program_representation.print_representation()

    def load_new_program(self, query):
        print('TODO')

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
                        self.load_new_program(query)
                    else:
                        scb_query = self.engine.convert_query(query)
                        scb_result = self.engine.process_query(scb_query)
                        scb_result.print_result()
                except SCBErrors.SCBInvalidQueryError:
                    print('Syntax Error - The entered query was not parsable!')
            self.exit_shell()
        except KeyboardInterrupt:
            self.exit_shell()

