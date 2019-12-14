import os
import re
import code_browsing.errors as SCBErrors
import code_browsing.program_representation as PR

class ProgramParser:

    def __init__(self, extension):
        self.extension = extension
        self.program_representation = None


    def parse_program_module(self, program_path):

        for _, d, f in os.walk(program_path):
            rel_path = os.path.join(d, f)
            if f.endswith(self.extension):
                self.parse_program(os.path.abspath(rel_path))


    def parse_lines_into_representation(self, lines):
        pass


    def parse_program(self, program_path):

        if not os.path.exists(program_path):
            raise OSError
        
        if os.path.isdir(program_path):
            self.parse_program_module(program_path)

        else:
            program_fp = open(program_path, 'r')
            program_lines = program_fp.readlines()
            program_fp.close()
            self.parse_lines_into_representation(program_lines)



class PrologProgramParser(ProgramParser):

    def __init__(self):
        super().__init__('.pl')
        self.program_representation = PR.PrologProgramRepresentation()
        self.possible_operands = ['+', 'is', '-', '=', '\\+', '\\=']



    def find_operands(self, symbol):
        operands = []
        for operand in possible_operands:
            if operand in symbol:
                operands.append(operand)
        return operands

    def grab_symbols(self, symbols_str):
        symbols = []
        current_symbol = ''
        nested_func_counter = 0
        for c in symbols_str:
            if c == '(':
                nested_func_counter = nested_func_counter + 1
            elif c == ')':
                nested_func_counter = nested_func_counter - 1
            if nested_func_counter == 0 and c == ',':
                symbols.append(current_symbol)
                current_symbol = ''
            else:
                current_symbol = current_symbol + c
        symbols.append(current_symbol)

        return symbols



    def convert_symbol_to_PR(self, symbol, is_predicate=False):
        symbol_no_whitespace = re.sub(' +', '', symbol.strip())
        print(symbol_no_whitespace)

        if '(' in symbol_no_whitespace and ')' in symbol_no_whitespace:
            term_list = []
            symbol_inputs = self.grab_symbols(symbol_no_whitespace.split('(', 1)[1][:-1])
            print(symbol_inputs)
            for elem in symbol_inputs:
                print(elem)
                term = self.convert_symbol_to_PR(elem)
                term_list.append(term)
            if is_predicate:
                return PR.Predicate(symbol_no_whitespace.split('(')[0], term_list, None)
            else:
                return PR.Function(symbol_no_whitespace.split('(')[0], term_list)
        else:
            items = symbol_no_whitespace.split('=')
            if len(items) == 1:
                computed_type = None
                if items[0][0].islower():
                    computed_type = 'atom'
                elif items[0][0] == '[':
                    computed_type = 'list'
                elif items[0][0].isdigit():
                    computed_type = 'scalar'
                elif items[0][0].isupper():
                    computed_type = 'var'
                return PR.Variable(items[0], computed_type)
            else:
                operations = self.find_operands(symbol_no_whitespace)
                operators = []
                for item in items:
                    computed_type = None
                    if item[0].islower():
                        computed_type = 'atom'
                    elif item[0] == '[':
                        computed_type = 'list'
                    elif item[0].isdigit():
                        computed_type = 'scalar'
                    operators.append(PR.Variable(item, computed_type))
                return PR.Operator('operator', operations, operators)


    def parse_lines_into_representation(self, program_lines):
        
        reading_predicate = False
        predicate = None
        predicate_body = []
        for line in program_lines:
            stripped = re.sub(' +', '', line.strip())

            # Case of single line predicate with no body
            if not reading_predicate and line.endswith('.') and ':-' not in line:
                temp = stripped[:-1]
                predicate = self.convert_symbol_to_PR(temp, is_predicate=True)

            # case of predicate
            if ':-' in line or stripped.endswith('.'):
                reading_predicate = True

            # Case of line with head + body
            if ':-' in line:
                head_body = stripped.split(':-')
                predicate = self.convert_symbol_to_PR(head_body[0], is_predicate=True)
                temp = head_body[1]
                if temp.endswith(','):
                    temp = temp[:-1]
                if temp.endswith('.'):
                    temp = temp[:-1]
                    reading_predicate = False
                if len(temp) > 0:
                    clauses = self.grab_symbols(temp)
                    for clause in clauses:
                        clause = self.convert_symbol_to_PR(clause)
                        if clause is not None:
                            predicate_body.append(clause)
                    
            elif reading_predicate:
                temp = line.strip()
                if temp.endswith('.'):
                    reading_predicate = False
                    temp = temp[:-1]
                elif temp.endswith(','):
                    temp = temp[:-1]
                for clause in temp.split(','):
                    clause, clause_vars, clause_functions = self.convert_symbol_to_PR(clause)
                    if clause is not None:
                        self.program_representation.add_function(clause)
                        predicate_body.append(clause)
                    if clause_vars is not None:
                        for var in clause_vars:
                            self.program_representation.add_variable(var)
                    if clause_functions is not None:
                        for func in clause_functions:
                            self.program_representation.add_function(func)

            if not reading_predicate:
                predicate.body = predicate_body
                try:
                    predicate.update_variable_expected_types()
                except SCBErrors.SCBVariableMatchInvalidError:
                    sys.stderr.write('WARNING: Variable in predicate {}/{} matches to two different conflicting types!\n'.format(predicate.name, predicate.arity))

                self.program_representation.add_predicate(predicate)
                self.program_representation.update_variable_expected_types()

                
