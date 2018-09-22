import re
import chardet
from os.path import basename
from PyQt5.QtWidgets import *
from collections import OrderedDict
import numpy as np


def import_decode(filename, **keypar):
    """import a encoded text file"""
    encoding = keypar.get('file_code')
    with open(filename, 'rb') as f:
        content = f.read()
        if encoding == 'auto':
            encoding = chardet.detect(content)['encoding']
            print(chardet.detect(content))
        content = content.decode(encoding)  # for encoding
        content = content.replace('\r\n', '\n')  # dos2unix
    return content


def xy_read(content, **keypar):
    """read (x, y) from a data content"""
    xy_format = keypar.get('xy_format')
    xy = re.compile(xy_format)
    x, y = [], []
    content = content.split("\n")
    for line in content:
        match = xy.match(line)
        if match:
            x.append(float(match.group(1)))
            y.append(float(match.group(2)))
    return (x, y)


def import_file(filename, **keypar):
    """ 
    import a single file & choose the part to plot
    """
    x, y = [], []
    content = import_decode(filename, **keypar)
    x, y = xy_read(content, **keypar)
    if x and y:
        return (x, y)
    else:
        return None


def chop_content(content, **keypar):
    """chop the file into different segments"""
    if keypar.get('head_ignore'):
        head_ignore = int(keypar.get('head_ignore'))
        content = re.split(r'\n', content)
        content = content[head_ignore:]
        content = "\n".join(content)
    else:
        pass
    if keypar.get('delimiter'):
        delimiter = keypar.get('delimiter')
        content = re.split(delimiter, content)
        content = list(map(lambda s: s.strip(), content))
    else:
        content = [content]  # nest the list for the subsequent combine @combine_list
    return content


def import_multiple_file(root, **keypar):
    """ 
    import multiple files, choose filenames on GUI
    root - the parent of the GUI
    ** additional key parameters:
            file_code       - unicode, gbk, etc. 
            xy_format       - how to obtain (x,y) data from each line
            no_segment      - flag that indicates there is only one segment
            head_ignore     - ignore some of the head lines
            split_segment   - flag that split the segments
            delimiter       - the delimiter of different segments
    """
    filename_list = QFileDialog.getOpenFileNames(root)[0]
    result = OrderedDict()
    for filename in filename_list:
        key = basename(filename)
        key = re.match('(.+)\.\w*', key).group(1)  # remove the surffix
        data = import_file(filename, **keypar)
        if keypar['no_segment'] is True or keypar['no_segment'] == 'True':
            if data:
                result[key] = np.array(data)
        elif keypar['split_segment'] is True or keypar['split_segment'] == 'True':
            content = import_decode(filename, **keypar)
            segment_contents = chop_content(content, **keypar)
            segment_keys = [key + '#{0}'.format(i + 1) for i in range(len(segment_contents))]
            segment_datas = [xy_read(segment_content, **keypar) for segment_content in segment_contents]
            for segment_key, segment_data in zip(segment_keys, segment_datas):
                result[segment_key] = np.array(segment_data)
        else:
            raise KeyError("conflict import parameters! -- one of 'no segment' and 'split segment' should be selected")
    return result
