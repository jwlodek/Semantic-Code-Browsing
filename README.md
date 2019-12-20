# Semantic Code Browsing

An implementation of [Semantic Code Browsing](https://arxiv.org/pdf/1608.02565.pdf) for CSE 505 at Stony Brook University.

### Introduction

Code  browsing  refers  to  the  process  of  searching  through  source  code  for  code  relating  to  particular  feature  or
implementation. This process can be as simple as finding sections of code that contain memory allocation, to identifying
where in code the left side of a binary tree is accessed. Traditionally, this process has relied on variable names and
in-source documentation. Most code browsing applications today search for keyword matches or some basic variable or
function names. As you may imagine, this approach has some core limitations: if code is not documented correctly
(such as comments copy pasted with functions that are then modified), then the code browser will return incorrect or
inconsistent results. Additionally, if documentation is lacking, or function and variable names are not verbose enough,
the modern code browser will not be able to assign any meaning to the attached code, simply skipping it, giving us the
possibility of missing correct results. Another common approach to code browsing that allows for more robust solutions
adds the use of regular expression based matching over simple keyword finding (see: Google Code Search), though
even these solutions will break down if the documentation surrounding the code is not sufficient.

### Usage

To start, you will need a `C` or `Prolog` program, and you will need `Python 3`. Start the shell by giving the path to
the program file as an argument:

```
PS E:\Stony Brook\09-Fall19\CSE 505\Semantic-Code-Browsing> py .\browse_code.py .\examples\larger_example.c
+----------------------------------------------------------------+
| Semantic-Code-Browsing                                         |
|----------------------------------------------------------------|
| SCB Query Shell v0.0.1                                         |
| C Single-File Program - .\examples\larger_example.c            |
| Jakub Wlodek - CSE 505 Final Project                           |
+----------------------------------------------------------------+

Welcome to the Semantic Code Browsing Query Shell. Please enter a valid query for the given program,
or see the documentation and/or examples for instructions on constructing valid queries.

SCB Query >
```

This will open the SCB Query Shell. From here you may construct queries to get semantic information about your program.

### Creating Queries

The format that queries entered into the query shell take is as follows:

* Each query begins with the find keyword.
* This is then followed by a search type, typically function or predicate with an optional arity marker.
* Then, optionally, assertions can be added by appending the where keyword followed by assertions of the following types. Each assertion starts with a keyword and colon, followed by certain search terms. Assertions can be glued together using or and and keywords.
    * inputs:INPUT_1_TYPE,INPUT_2_TYPE...
    * bodycontains:SEARCHTYPE (SEARCHTYPE: function, loop, conditional)
    * returns:RETURN_TYPE
* All queries end with a period.

Below are some examples of valid queries on an input program:

```
SCB Query > find function/2 where inputs:int,char* or returns:void.
SCB Query > find predicate.
SCB Query > find predicate where bodycontains:function and inputs:function/3,var.
SCB Query > find function where bodycontains:loop and returns:int*.
```

### Example Results

Find all functions in program
```
SCB Query > find functions.

Searching for functions that satisfy assertions:
No arity specified of target function or predicate.

Query: find functions.

 > Function Name: check_id_repeat Function arity: 2 Returns: int
 > Function Name: search_by_id Function arity: 2 Returns: struct student_records*
 > Function Name: search_by_name Function arity: 2 Returns: int*
 > Function Name: search_by_major Function arity: 2 Returns: int*
 > Function Name: fix_names Function arity: 1 Returns: void
 > Function Name: fix_majors Function arity: 1 Returns: void
 > Function Name: print_student Function arity: 3 Returns: void
 > Function Name: print_all_students Function arity: 3 Returns: void
 > Function Name: free_list Function arity: 1 Returns: void

9 Matching result(s) found.
```
Find all functions with int return type
```
SCB Query > find functions where returns:int.

Searching for functions that satisfy assertions:
 - Assertion: returns -> ['int']
No arity specified of target function or predicate.

Query: find functions where returns:int.

 > Function Name: check_id_repeat Function arity: 2 Returns: int

1 Matching result(s) found.
```
Find all functions with loops (useful for optimization)
```
SCB Query > find functions where bodycontains:loop.

Searching for functions that satisfy assertions:
 - Assertion: bodycontains -> ['loop']
No arity specified of target function or predicate.

Query: find functions where bodycontains:loop.

 > Function Name: fix_names Function arity: 1 Returns: void
 > Function Name: fix_majors Function arity: 1 Returns: void
 > Function Name: print_all_students Function arity: 3 Returns: void
 > Function Name: free_list Function arity: 1 Returns: void

4 Matching result(s) found.
```