import re
from collections import defaultdict
import os
import sys
from pathlib import Path
import ast


def too_long(line, lines, file_messages):
    if len(line) > 79:
        file_messages[lines.index(line) + 1].append(': S001 Too long')


def indentation(line, lines, file_messages):
    if ' ' == line[0]:
        if (len(line) - len(line.lstrip(' '))) % 4 != 0:
            file_messages[lines.index(line) + 1].append(': S002 Indentation is not a multiple of four')


def semicolon(line, lines, file_messages):
    parts_of_line = line.split('#')
    temporary_line = parts_of_line[0].rstrip()
    if len(temporary_line) > 1 and temporary_line[-1] == ';':
        file_messages[lines.index(line) + 1].append(': S003 Unnecessary semicolon')


def at_least_spaces(line, lines, file_messages):
    if '#' in line:
        if '#' != line[0]:
            parts_of_line = line.split('#')
            if (len(parts_of_line[0]) - len(parts_of_line[0].rstrip(' '))) < 2:
                file_messages[lines.index(line) + 1].append(': S004 At least two spaces required before inline comments')


def todo(line, lines, file_messages):
    if '#' in line:
        parts_of_line = line.split('#')
        if 'todo' in parts_of_line[1].lower():
            file_messages[lines.index(line) + 1].append(': S005 TODO found')


def check_construction(line, lines, file_messages):
    try:
        pattern = re.compile(r"^\s*(class|def)(\s+)(\w+)[(:]")
        match = pattern.search(line)
        if not match:
            return
    except IndexError:
        return
    construction = match.group(1)
    spaces = match.group(2)
    name = match.group(3)
    if spaces != " ":
        file_messages[lines.index(line) + 1].append(f': S007 Too many spaces after \'{construction}\'')
    if construction == "class":
        if not re.match(r'^[A-Z][a-zA-Z0-9]*$', name):
            file_messages[lines.index(line) + 1].append(f': S008 Class name \'{name}\' should use CamelCase')
    elif construction == "def":
        if not re.match(r'^[a-z_][a-z0-9_]*$', name):
            file_messages[lines.index(line) + 1].append(f': S009 Function name \'{name}\' should use snake_case')


def too_more_blank_lines(lines, file_messages):
    number_of_blank_lines_preceding_a_code = 0
    for i, line in enumerate(lines):
        if len(line.strip()) == 0:
            number_of_blank_lines_preceding_a_code += 1
        else:
            if number_of_blank_lines_preceding_a_code > 2:
                file_messages[i + 1].append(': S006 More than two blank lines preceding a code line')
            number_of_blank_lines_preceding_a_code = 0


def arguments_and_variables(lines, file_messages):
    try:
        tree = ast.parse(''.join(lines))
        for node in ast.walk(tree):
                # Sprawdzanie nazw funkcji
            if isinstance(node, ast.FunctionDef):
                for arg in node.args.args:
                    if not re.match(r'^[a-z_][a-z0-9_]*$', arg.arg):
                        file_messages[node.lineno].append(f': S010 Argument name \'{arg.arg}\' should be written in snake_case')

                    # Sprawdzanie argumentów domyślnych
                for default in node.args.defaults:
                    if isinstance(default, (ast.List, ast.Dict, ast.Set)):
                        file_messages[node.lineno].append(f': S012 The default argument value is mutable')

                # Sprawdzanie zmiennych
            if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
                if not re.match(r'^[a-z_][a-z0-9_]*$', node.id):
                    file_messages[node.lineno].append(f': S011 Variable name \'{node.id}\' should be written in snake_case')
    except SyntaxError:
        pass  # Ignorujemy błędy składni, które mogą wystąpić podczas parsowania


def analyze_file(path_file):
    file_messages = defaultdict(list)
    with open(path_file) as file:
        lines = file.readlines()
        for line in lines:
            too_long(line, lines, file_messages)
            indentation(line, lines, file_messages)
            semicolon(line, lines, file_messages)
            at_least_spaces(line, lines, file_messages)
            todo(line, lines, file_messages)
            check_construction(line, lines, file_messages)
        too_more_blank_lines(lines, file_messages)
        arguments_and_variables(lines, file_messages)
    return file_messages


def print_message(file_messages, item):
    for line_num in sorted(file_messages):
        file_messages[line_num] = list(dict.fromkeys(file_messages[line_num]))
        for message in sorted(file_messages[line_num]):
            print(str(item) + ': Line ' + str(line_num) + message)


arg = sys.argv
path = ' '.join(arg[1:])

if os.path.isdir(path):
    path = Path(path)
    files_in_path = path.iterdir()
    for item in files_in_path:
        if item.is_file():
            if str(item).endswith('.py'):
                file_messages = analyze_file(item)
                if file_messages:
                    print_message(file_messages, item)
else:
    if str(path).endswith('.py'):
        file_messages = analyze_file(path)
        if file_messages:
            print_message(file_messages, path)