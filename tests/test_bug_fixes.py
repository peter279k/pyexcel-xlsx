"""

  This file keeps all fixes for issues found

"""
import os
import sys
import datetime
import psutil
from textwrap import dedent
import pyexcel as pe
from pyexcel_xlsx.xlsxr import get_columns
from pyexcel.internal.sheets._shared import excel_column_index
from nose.tools import eq_
from platform import python_implementation


PY36_ABOVE = sys.version_info[0] == 3 and sys.version_info[1] >= 6


def test_pyexcel_issue_4():
    """pyexcel issue #4"""
    indices = [
        'A',
        'AA',
        'ABC',
        'ABCD',
        'ABCDE',
        'ABCDEF',
        'ABCDEFG',
        'ABCDEFGH',
        'ABCDEFGHI',
        'ABCDEFGHIJ',
        'ABCDEFGHIJK',
        'ABCDEFGHIJKL',
        'ABCDEFGHIJKLM',
        'ABCDEFGHIJKLMN',
        'ABCDEFGHIJKLMNO',
        'ABCDEFGHIJKLMNOP',
        'ABCDEFGHIJKLMNOPQ',
        'ABCDEFGHIJKLMNOPQR',
        'ABCDEFGHIJKLMNOPQRS',
        'ABCDEFGHIJKLMNOPQRST',
        'ABCDEFGHIJKLMNOPQRSTU',
        'ABCDEFGHIJKLMNOPQRSTUV',
        'ABCDEFGHIJKLMNOPQRSTUVW',
        'ABCDEFGHIJKLMNOPQRSTUVWX',
        'ABCDEFGHIJKLMNOPQRSTUVWXY',
        'ABCDEFGHIJKLMNOPQRSTUVWXYZ',
    ]
    for column_name in indices:
        print("Testing %s" % column_name)
        column_index = excel_column_index(column_name)
        new_column_name = get_columns(column_index)
        print(column_index)
        print(column_name)
        print(new_column_name)
        assert new_column_name == column_name


def test_pyexcel_issue_5():
    """pyexcel issue #5

    datetime is not properly parsed
    """
    s = pe.get_sheet(file_name=get_fixtures("test-date-format.xls"))
    s.save_as("issue5.xlsx")
    s2 = pe.load("issue5.xlsx")
    assert s[0, 0] == datetime.datetime(2015, 11, 11, 11, 12, 0)
    assert s2[0, 0] == datetime.datetime(2015, 11, 11, 11, 12, 0)


def test_pyexcel_issue_8_with_physical_file():
    """pyexcel issue #8

    formular got lost
    """
    tmp_file = "issue_8_save_as.xlsx"
    s = pe.get_sheet(file_name=get_fixtures("test8.xlsx"))
    s.save_as(tmp_file)
    s2 = pe.load(tmp_file)
    eq_(str(s), str(s2))
    content = dedent("""
    CNY:
    +----------+----------+------+---+-------+
    | 01/09/13 | 02/09/13 | 1000 | 5 | 13.89 |
    +----------+----------+------+---+-------+
    | 02/09/13 | 03/09/13 | 2000 | 6 | 33.33 |
    +----------+----------+------+---+-------+
    | 03/09/13 | 04/09/13 | 3000 | 7 | 58.33 |
    +----------+----------+------+---+-------+""").strip("\n")
    eq_(str(s2), content)
    os.unlink(tmp_file)


def test_pyexcel_issue_8_with_memory_file():
    """pyexcel issue #8

    formular got lost
    """
    tmp_file = "issue_8_save_as.xlsx"
    f = open(get_fixtures("test8.xlsx"), "rb")
    s = pe.load_from_memory('xlsx', f.read())
    s.save_as(tmp_file)
    s2 = pe.load(tmp_file)
    eq_(str(s), str(s2))
    content = dedent("""
    CNY:
    +----------+----------+------+---+-------+
    | 01/09/13 | 02/09/13 | 1000 | 5 | 13.89 |
    +----------+----------+------+---+-------+
    | 02/09/13 | 03/09/13 | 2000 | 6 | 33.33 |
    +----------+----------+------+---+-------+
    | 03/09/13 | 04/09/13 | 3000 | 7 | 58.33 |
    +----------+----------+------+---+-------+""").strip("\n")
    eq_(str(s2), content)
    os.unlink(tmp_file)


def test_excessive_columns():
    tmp_file = "date_field.xlsx"
    s = pe.get_sheet(file_name=get_fixtures(tmp_file))
    assert s.number_of_columns() == 2


def test_issue_8_hidden_sheet():
    test_file = get_fixtures("hidden_sheets.xlsx")
    book_dict = pe.get_book_dict(file_name=test_file,
                                 library="pyexcel-xlsx")
    assert "hidden" not in book_dict
    eq_(book_dict['shown'], [['A', 'B']])


def test_issue_8_hidden_sheet_2():
    test_file = get_fixtures("hidden_sheets.xlsx")
    book_dict = pe.get_book_dict(file_name=test_file,
                                 skip_hidden_sheets=False,
                                 library="pyexcel-xlsx")
    assert "hidden" in book_dict
    eq_(book_dict['shown'], [['A', 'B']])
    eq_(book_dict['hidden'], [['a', 'b']])


def test_issue_14_xlsx_file_handle():
    if python_implementation == 'PyPy':
        return
    if PY36_ABOVE:
        return
    proc = psutil.Process()
    test_file = os.path.join("tests", "fixtures", "hidden_sheets.xlsx")
    open_files_l1 = proc.open_files()

    # start with a csv file
    data = pe.iget_array(file_name=test_file, library='pyexcel-xlsx')
    open_files_l2 = proc.open_files()
    delta = len(open_files_l2) - len(open_files_l1)
    # interestingly, file is already open :)
    assert delta == 1

    # now the file handle get opened when we run through
    # the generator
    list(data)
    open_files_l3 = proc.open_files()
    delta = len(open_files_l3) - len(open_files_l1)
    # caught an open file handle, the "fish" finally
    assert delta == 1

    # free the fish
    pe.free_resources()
    open_files_l4 = proc.open_files()
    # this confirms that no more open file handle
    eq_(open_files_l1, open_files_l4)


def test_issue_83_file_handle_no_generator():
    if python_implementation == 'PyPy':
        return
    proc = psutil.Process()
    test_files = [
        os.path.join("tests", "fixtures", "hidden_sheets.xlsx")
    ]
    for test_file in test_files:
        open_files_l1 = proc.open_files()
        # start with a csv file
        pe.get_array(file_name=test_file)
        open_files_l2 = proc.open_files()
        delta = len(open_files_l2) - len(open_files_l1)
        # no open file handle should be left
        assert delta == 0


def get_fixtures(file_name):
    return os.path.join("tests", "fixtures", file_name)
