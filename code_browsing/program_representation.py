import sys
import code_browsing.errors as SCBErrors

class ProgramRepresentation:

    def __init__(self, name, description):
        self.representation_name = name
        self.description = description


class PrologProgramRepresentation(ProgramRepresentation):

    def __init__(self):
        super().__init__('Prolog Representation', 'Prolog Program represented as series of predicates.')
        self.predicates = []
        self.predicate_map = {}

    def update_variable_expected_types(self, predicate):
        matching_predicates = []
        for pred in self.predicates:
            if pred.name == predicate.name:
                if pred.arity != predicate.arity:
                    raise SCBErrors.SCBRedefinedPredicateError
                else:
                    matching_predicates.append(pred)

        for pred in matching_predicates:
            for i in range(0, len(pred.set_of_terms)):
                if isinstance(pred.set_of_terms[i], Function) and isinstance(predicate.set_of_terms[i], Variable):
                    if predicate.set_of_terms[i].computed_type == 'var' or predicate.set_of_terms[i].computed_type is None:
                        predicate.set_of_terms[i].computed_type = 'func'
                    else:
                        raise SCBErrors.SCBVariableMatchInvalidError
                elif isinstance(pred.set_of_terms[i], Variable) and isinstance(predicate.set_of_terms[i], Function):
                    if pred.set_of_terms[i].computed_type == 'var' or pred.set_of_terms[i].computed_type is None:
                        pred.set_of_terms[i].computed_type = 'func'
                    else:
                        raise SCBErrors.SCBVariableMatchInvalidError
                elif isinstance(pred.set_of_terms[i], Variable) and isinstance(predicate.set_of_terms[i], Variable):
                    if pred.set_of_terms[i].computed_type is None:
                        pred.set_of_terms[i].computed_type = predicate.set_of_terms[i].computed_type
                    elif predicate.set_of_terms[i].computed_type is None:
                        predicate.set_of_terms[i].computed_type = pred.set_of_terms[i].computed_type
                    elif pred.set_of_terms[i].computed_type == 'var' and predicate.set_of_terms[i].computed_type != 'var':
                        pred.set_of_terms[i].computed_type = predicate.set_of_terms[i].computed_type
                    elif predicate.set_of_terms[i].computed_type == 'var' and pred.set_of_terms[i].computed_type != 'var':
                        predicate.set_of_terms[i].computed_type = pred.set_of_terms[i].computed_type
                    elif predicate.set_of_terms[i].computed_type != pred.set_of_terms[i].computed_type:
                        raise SCBErrors.SCBVariableMatchInvalidError



    def add_predicate(self, new_pred):
        self.predicates.append(new_pred)
        self.predicate_map[new_pred.name] = len(self.predicates) - 1

    def print_representation(self, fp=sys.stdout):
        fp.write('{} w/ {} predicates\n{}\nPredicates:\n'.format(self.representation_name, len(self.predicates), self.description))
        for pred in self.predicates:
            pred.print_term(fp=fp)

class PythonProgramRepresentation:
    #TODO
    pass

class CProgramRepresentation:
    #TODO
    pass

class Term:

    def __init__(self, name):
        self.name = name

    def print_term(self, fp=sys.stdout):
        fp.write('Term name: {}\n'.format(self.name))


class Operator(Term):

    def __init__(self, name, operations, operators):
        super().__init__(name)
        self.operations = operations
        self.operators = operators

    def print_term(self, fp=sys.stdout):
        fp.write('Performing operations:\n')
        for operation in self.operations:
            fp.write('{} '.format(operation))
        fp.write('\nbetween:\n')
        for term in self.operators:
            term.print_term(fp=fp)
        fp.write('----------\n')


class Variable(Term):

    def __init__(self, name, computed_type):
        super().__init__(name)
        self.computed_type = computed_type

    def get_variable_list_from_terms(self):
        out = []
        out.append(self)
        return out

    def print_term(self, fp=sys.stdout):
        expected_type = self.computed_type
        if self.computed_type is None:
            expected_type = 'Unknown'
        fp.write('Variable: {}, Expected Type: {}\n'.format(self.name, expected_type))


class Function(Term):

    def __init__(self, name, set_of_terms):
        super().__init__(name)
        self.arity = len(set_of_terms)
        self.set_of_terms = set_of_terms

    def get_variable_list_from_terms(self):
        variable_list = []
        for term in self.set_of_terms:
            if isinstance(term, Variable):
                variable_list.append(term)
            else:
                variable_list = variable_list + term.get_variable_list_from_terms()
        return variable_list

    def print_term(self, fp=sys.stdout):
        super().print_term()
        fp.write('Function of arity {}\nTerms:\n'.format(self.arity))
        for term in self.set_of_terms:
            term.print_term(fp=fp)
        fp.write('----------\n')

class PythonFunction(Function):

    def __init__(self, name, set_of_terms, return_set):
        super().__init__(name, set_of_terms)
        self.return_set = return_set


class Predicate(Function):

    def __init__(self, name, set_of_terms, body):
        super().__init__(name, set_of_terms)
        self.body = body

    def get_variable_list_from_terms(self):
        variable_list = super().get_variable_list_from_terms()
        for term in self.body:
            if isinstance(term, Variable):
                variable_list.append(term)
            else:
                variable_list = variable_list + term.get_variable_list_from_terms()
        return variable_list


    def update_variable_expected_types(self):
        variable_list = self.get_variable_list_from_terms()
        for var in variable_list:
            for v2 in variable_list:
                if var.name == v2.name:
                    if var.computed_type is None:
                        var.computed_type = v2.computed_type
                    elif v2.computed_type is None:
                        v2.computed_type = var.computed_type
                    elif var.computed_type == 'var' and v2.computed_type != 'var':
                        var.computed_type = v2.computed_type
                    elif v2.computed_type == 'var' and var.computed_type != 'var':
                        v2.computed_type = var.computed_type
                    elif var.computed_type != v2.computed_type:
                        raise SCBErrors.SCBVariableMatchInvalidError



    def print_term(self, fp=sys.stdout):
        fp.write('Predicate {}\n'.format(self.name))
        super().print_term()
        fp.write('Body of predicate:\n')
        for term in self.body:
            term.print_term(fp=fp)
        fp.write('----------\n')