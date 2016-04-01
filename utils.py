# -*- encode:utf-8 -*-
from const import *
import re


def is_vector_define(line):
    if not line:
        return None
    result = re.match(ValuePattern.value_pattern_vector, line)
    if not result:
        return None
    if not result.groupdict().get(ValuePattern.value_name):
        return None
    '''can't solve pointer type'''
    if "*" in result.groupdict().get(ValuePattern.value_type_name):
        return None
    return result.groupdict()


def is_value_define(line):
    if not line:
        return None
    result = re.match(ValuePattern.value_name_defineline_pattern, line)
    if not result:
        return None
    if not result.groupdict().get(ValuePattern.value_name):
        return None
    return result.groupdict()


def is_start_or_end_of_struct(line):
    if not line:
        return None
    result = re.match(r'^\}.*', line)
    if result:
        return "}"
    result = re.match(r'^\{.*', line)
    if result:
        return "{"

    return None


def is_structhead(line):
    if not line:
        return None
    result = re.match(StructPattern.struct_name_pattern, line)
    if not result:
        return None

    return result.groupdict().get(StructPattern.struct_name)


'''travel the file by lines, pick all the value with the start of "TOBYTES" '''


def read_eight_length_macro(srcfile):

    with open(srcfile, "r") as infile:
        if not infile:
            return

        while True:
            line = infile.readline()
            if not line:
                break
            e_name = is_tobytes(line)
            if not e_name:
                continue
            if e_name not in Constants.eight_length_value:
                Constants.eight_length_value.append(e_name)


'''match the line started with "TOBYTES" '''


def is_tobytes(line):
    pattern = r'^%s( *):( *)(?P<eName>(%s))' % (Constants.TOBYTES, CommonPattern.length_name_pattern)
    result = re.match(pattern, line)
    if not result:
        return None
    e_name = result.groupdict().get("eName")
    return e_name


def get_line_type(line):
    if not line:
        return LineType.LINE_OTHER
    result = is_structhead(line)
    if result:
        return LineType.LINE_STRUCT
    result = is_start_or_end_of_struct(line)
    if result:
        return LineType.LINE_STARTOREND_STRUCT

    result = is_vector_define(line)
    if result:
        return LineType.LINE_VECTOR

    result = is_value_define(line)
    if result:
        if not result.get(ValuePattern.value_type_array_length_dimen_one):
            if '' == result.get(ValuePattern.value_type_name):
                return LineType.LINE_OTHER
            return LineType.LINE_VALUE
        else:
            return LineType.LINE_ARRAY
    return LineType.LINE_OTHER
