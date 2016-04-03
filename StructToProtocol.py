# -*- encode:utf-8 -*-

'''
author : s00357558 shenweimin
function :  convert struct to proto
problems:   1,can't recognize two-dimension array
            2,can't recognize enum
            3,types in type_map is not enough
how to use: 1, build ".struct " file: put all valid struct in a .struct file
            2, put the 8bytes variable on the front of the file marked by "TOBYTES",for example: TOBYTES:VRM_MAX_ID_LEN
            3, create folder "struct",and put all .struct to be transformed in it.
            4, use command: python StructToProto.py struct/
            5, all the results named *.proto will be restored in the folder named "proto" in current dictionary
'''

import os
import os.path
import sys
import logging

from utils import *

'''init logging'''
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
                    datefmt='%a, %d %b %Y %H:%M:%S',
                    filename='spm_pb.log',
                    filemode='w')

console = logging.StreamHandler()
console.setLevel(logging.INFO)
formatter = logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s')
console.setFormatter(formatter)
logging.getLogger('').addHandler(console)


def proc_line_struct(line):
    result = is_structhead(line)
    if not result:
        return ""
    else:
        new_line = "message " + result + "\n"
        return new_line


def proc_line_start_or_end_of_struct(line):
    result = is_start_or_end_of_struct(line)
    if not result:
        return ""

    new_line = result + "\n"
    return new_line


def proc_line_error(line, total_line_no, readfile):
    new_line = ""
    if is_tobytes(line):
        pass
    elif re.match(r'^\s*$',line):
        new_line = line
    elif re.match(r'/\*.*\*/',line):
        pass
    else:
        logging.error("line[" + str(total_line_no) + "] " + "file[" + readfile + "]")
        new_line = ">>>>>>>>>>\n" + line + "<<<<<<<<<<\n"
    return new_line


def proc_line_vector(line, value_seq_no):
    result = is_vector_define(line)
    v_type = result.get(ValuePattern.value_type_name)
    v_name = result.get(ValuePattern.value_name)
    proto_type = vector_type_map.get(v_type)
    if not proto_type:
        proto_type = v_type

    new_line = "{0}repeated {1} {2} = {3};\n".format(Constants.PRE_BLANK, proto_type, v_name,
                                                     str(value_seq_no))
    return new_line


def proc_line_value(line, value_seq_no):
    result = is_value_define(line)
    v_type = result.get(ValuePattern.value_type_name)
    v_name = result.get(ValuePattern.value_name)
    proto_type = type_map.get(v_type)
    '''solved: if contents pointer'''
    if '*' in v_type or '*' in v_name:
        v_type = 'int64'
        proto_type = v_type
        if '*' in v_name:
            v_name = v_name[1:]
    elif not proto_type:
        type_map[v_type] = v_type
        proto_type = v_type
    new_line = "{0}optional {1} {2} = {3};\n".format(Constants.PRE_BLANK, proto_type, v_name,
                                                     str(value_seq_no))
    return new_line


def proc_line_array(line, value_seq_no):
    result = is_value_define(line)
    v_type = result.get(ValuePattern.value_type_name)
    v_name = result.get(ValuePattern.value_name)
    length_name = result.get(ValuePattern.value_type_array_length_dimen_one)
    line_type = "repeated "
    proto_type = type_map.get(v_type)
    if not proto_type:
        type_map[v_type] = v_type
        proto_type = v_type
    elif v_type == 'VOS_UCHAR' or v_type == 'VOS_CHAR':
        line_type = "optional "
        if length_name in Constants.eight_length_value:
            proto_type = "bytes "
        else:
            proto_type = "string "
    new_line = "{0}{1}{2} {3} = {4};\n".format(Constants.PRE_BLANK, line_type, proto_type, v_name,
                                               str(value_seq_no))
    '''situation: two dimension'''
    two_dimen_length = result.get(ValuePattern.value_type_array_length_dimen_two)

    if two_dimen_length:
        line_type = "repeated "
        if two_dimen_length in Constants.eight_length_value:
            proto_type = "bytes "
        else:
            proto_type = "string "
        new_line = "{0}{1}{2} {3} = {4};\n".format(Constants.PRE_BLANK, line_type, proto_type, v_name,
                                                   str(value_seq_no))

    return new_line

'''convert structs from 'readfile' to protocol store in 'writefile'''''


def struct_to_proto(readfile, writefile):
    read_eight_length_macro(readfile)
    with open(readfile, "r") as infile:
        new_file_content = []
        value_seq_no = 0
        total_line_no = 0
        while True:
            new_line = ""
            line = infile.readline()
            if not line:
                break
            '''delete comment after ';'''''
            pos = line.find(';')
            if -1 != pos:
                line = line[0:pos + 1]
            ''' ignore comment'''
            tmp_line = line.lstrip()
            if tmp_line.startswith("//") or tmp_line.startswith("/*"):
                continue

            total_line_no += 1
            line_type = get_line_type(line)
            '''if the start of structure'''
            if line_type == LineType.LINE_STRUCT:
                new_line = proc_line_struct(line)

            elif line_type == LineType.LINE_STARTOREND_STRUCT:
                value_seq_no = 0
                new_line = proc_line_start_or_end_of_struct(line)

            elif line_type == LineType.LINE_ARRAY:
                value_seq_no += 1
                new_line = proc_line_array(line, value_seq_no)

            elif line_type == LineType.LINE_VALUE:
                value_seq_no += 1
                new_line = proc_line_value(line, value_seq_no)

            elif line_type == LineType.LINE_VECTOR:
                value_seq_no += 1
                new_line = proc_line_vector(line, value_seq_no)

            elif line_type == LineType.LINE_OTHER:
                new_line = proc_line_error(line, total_line_no, readfile)

            new_file_content.append(new_line)

    with open(writefile, "w") as outfile:
        outfile.writelines(new_file_content)


def main():
    Constants.eight_length_value.append(Constants.COMMON_MACRO)
    if len(sys.argv) < 2:
        struct_dir = os.path.join(os.getcwd(), "struct")
    else:
        struct_dir = os.path.join(os.getcwd(), sys.argv[1])
    if not os.path.exists(struct_dir):
        print str(sys.argv), " not exist"
        exit()
    proto_dir = os.path.join(os.getcwd(), "proto")
    if not os.path.exists(proto_dir):
        os.mkdir(proto_dir)
    for parent, dirnames, filenames in os.walk(struct_dir):
        for filename in filenames:
            readfile = os.path.join(parent, filename)
            '''write_file_name = filename + ".proto"'''
            write_file_name = 'pb_' + filename + ".proto"
            writefile = os.path.join(proto_dir, write_file_name)
            struct_to_proto(readfile, writefile)


if __name__ == "__main__":
    exit(main())

