# Copyright (c) 2022 konstvest

# This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.

#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.

#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
from argparse import ArgumentError
import re
import hashlib #for md5
from struct import pack, unpack

class CByteReader:
    def __init__(self, raw_data):
        self._offset=0
        self._raw_data = raw_data
        self._format_table = {'d':8, 'i':4,'f':4 ,'h':2, 's':1}

    def _sizeof(self, format_string):
        size = 0
        for char in format_string:
            size += self._format_table[char]
        return size

    def read(self, format):
        size = self._sizeof(format)
        value = unpack(format, self._raw_data[self._offset:self._offset+size])
        if 's'*len(format) == format:
            #string
            value = b''.join(value)
        if len(value) == 1:
            value = value[0]
        
        self._offset += size
        return value

    def is_EOF(self):
        return len(self._raw_data) == self._offset

    def data(self):
        return self._raw_data

class CItemGroup:
    def __init__(self, type, mask, uv_convert_count, ei_group, t_number, c_count, uv_base=None):
        self.type : str = type
        self.mask = mask #regexpr
        self.uv_convert_count : int = uv_convert_count
        self.ei_group : int = ei_group
        self.t_number : int = t_number
        self.morph_component_count : int = c_count #{1 or 8} experimental for easy import\export for user
        self.uv_base = uv_base or (0, 1)

class CItemGroupContainer:
    def __init__(self):
        self.item_type : list[CItemGroup] = [
            #TODO: check from models
            CItemGroup('quest, quick, material', re.compile(r'init(li)?(qu|qi|tr|mt)[0-9]+'), 0, 19, 8, 1, uv_base=(-1, -1))
            #CItemGroup('quest, quick, material', re.compile(r'init(li)?(qu|qi|tr|mt)[0-9]+'), 0, 19, 8, 1)
            ,CItemGroup('treasure/loot', re.compile(r'inittr[0-9]+'), 0, 18, 8, 1, uv_base=(-1, -1))
            #,CItemGroup('shop weapons/armors', re.compile(r'init(we|ar)[a-zA-Z]+[0-9]+'), 1, 18, 8, 1)
            ,CItemGroup('shop weapons/armors', re.compile(r'init(we|ar)[a-zA-Z]+[0-9]+'), 0, 18, 8, 1, uv_base=(-1, -1))
            #,CItemGroup('shop weapons/armors2', re.compile(r'armor\D+'), 1, 18, 8, 1)
            ,CItemGroup('interactive game objects', re.compile(r'ingm[0-9]+'), 0, 22, 8, 1)
            ,CItemGroup('faces',            re.compile(r'infa[0-9]+'), 0, 22, 8, 1)
            # ,CItemGroup('weapons',          re.compile(r'(\.(pike|sword|dagger|2axe|club|axe|crbow|bw\D+)|^crbow|^bw\D+)\d+'), 0, 18, 2, 8)
            #,CItemGroup('weapons left', re.compile(r'(lh3\.(pike|sword|dagger|2axe|club|axe|crbow|bw\D+)|^crbow|^bw\D+)\d+'), 1, 18, 2, 8, uv_base=(0, 0))
            #,CItemGroup('weapons right',   re.compile(r'(\.(pike|sword|dagger|2axe|club|axe|crbow|bw\D+)|^crbow|^bw\D+)\d+'), 1, 18, 2, 8, uv_base=(0, 0))
            #,CItemGroup('helms', re.compile(r'hd\.armor\d+'), 1, 19, 2, 8, uv_base=(0, 0))
            #,CItemGroup('shield', re.compile(r'lh2\.shield\d+'), 1, 18, 2, 8, uv_base=(0, 0))            

            ,CItemGroup('arrows',   re.compile(r'quiver|arrow(s|00)'), 1, 19, 2, 8, uv_base=(0, 1))
            ,CItemGroup('archery', re.compile(r'(\.(crbow|bw\D+)|^crbow|^bw\D+)\d+'), 1, 18, 2, 8, uv_base=(0, 1))
            ,CItemGroup('archery2', re.compile(r'(\.(crbow..part|bw..part\D+)|^crbow..part|^bw..part\D+)\d+'), 1, 18, 2, 8, uv_base=(0, 1))
            ,CItemGroup('shield', re.compile(r'lh2\.axe\d+'), 1, 18, 2, 8, uv_base=(1, 1))
            ,CItemGroup('exshield', re.compile(r'lh2\.shield\d+'), 1, 18, 2, 8, uv_base=(1, 1))
            ,CItemGroup('staffleft',     re.compile(r'lh3\.staff\D+'), 1, 18, 2, 8, uv_base=(1, 1))
            ,CItemGroup('stafflefttwo',  re.compile(r'lh3\.dstaff\D+'), 1, 18, 2, 8, uv_base=(1, 1))
            ,CItemGroup('staffright',    re.compile(r'rh3\.staff\D+'), 1, 18, 2, 8, uv_base=(0, 1))
            ,CItemGroup('staffrighttwo', re.compile(r'rh3\.dstaff\D+'), 1, 18, 2, 8, uv_base=(0, 1))
            ,CItemGroup('weapons left', re.compile(r'(lh3\.(pike|dpike|sword|dsword|dagger|club|dclub|axe|daxe|staff|dstaff|shit1|shit2\D+)|^shit1|^shit2\D+)\d+'), 1, 18, 2, 8, uv_base=(1, 1))
            ,CItemGroup('weapons',   re.compile      (r'(\.(pike|dpike|sword|dsword|dagger|club|dclub|axe|daxe|staff|dstaff|crbow|bw\D+)|^crbow|^bw\D+)\d+'), 1, 18, 2, 8, uv_base=(0, 1))
            ,CItemGroup('helms', re.compile(r'hd\.armor\d+'), 1, 19, 2, 8, uv_base=(0, 0))

            #,CItemGroup('weapons left', re.compile(r'((lh3.pike|lh3.sword|lh3.dagger|lh3.2axe|lh3.club|lh3.axe|lh3.crbow|bw\D+)|^lh3.crbow|^lh3.bw\D+)\d+'), 1, 18, 2, 8, uv_base=(1, 1))
            #,CItemGroup('weapons',   re.compile(r'((rh3.pike|rh3.sword|rh3.dagger|rh3.2axe|rh3.club|rh3.axe|rh3.crbow|rh3.bw\D+)|^rh3.crbow|^rh3.bw\D+)\d+'), 1, 18, 2, 8, uv_base=(0, 1))
            #,CItemGroup('helms', re.compile(r'hd\.armor\d+'), 1, 19, 2, 8, uv_base=(0, 0))
            #,CItemGroup('shield', re.compile(r'lh2.shield\d+'), 1, 18, 2, 8, uv_base=(1, 0))

            ,CItemGroup('armr',            re.compile(r'\.armor\d+'), 0, 19, 1, 8)
            ,CItemGroup('unit',             re.compile(r'un(an|mo|hu|or|sk).+'), 0, 19, 1, 8)

            ,CItemGroup('world objects', re.compile(r'.+'), 0, 18, 8, 8) #LAST
            ]
    
    def get_item_group(self, obj_name: str):
        for item in self.item_type:
            if item.mask.search(obj_name) is not None:
                print("FOUND", obj_name)    
                return item
        print("NOT FOUND", obj_name)    
        #assert!!!!
        return None


def get_uv_convert_count(name: str):
    '''
    gets count of convert uv coordinates depending on filename
    '''
    container = CItemGroupContainer()
    return container.get_item_group(name).uv_convert_count

def get_uv_params(name: str):
    container = CItemGroupContainer()
    group = container.get_item_group(name)
    return group.uv_convert_count, group.uv_base

def get_uv_group_name(name: str):
    container = CItemGroupContainer()
    group = container.get_item_group(name)
    return group.type

def get_uv_base(name: str):
    container = CItemGroupContainer()
    group = container.get_item_group(name)
    return group.uv_base


def sumVector(vec1, vec2):
    if len(vec1) != len(vec2):
        raise ArgumentError

    result = []
    for i in range(len(vec2)):
        result.append(vec1[i] + vec2[i])
    return result

def subVector(vec1, vec2): #subtract vec2 from vec1
    if len(vec1) != len(vec2):
       raise ArgumentError

    result = []
    for i in range(len(vec2)):
        result.append(vec1[i] - vec2[i])
    return result

def mulVector(vec1, scalar): #multiply vector with scalar
    result = []
    for i in range(len(vec1)):
        result.append(vec1[i] * scalar)
    return result

def unpack_uv(uv_, count, uv_base=None):
    '''
    increases x,y value 2 times per side and offset by y(vertically)
    '''
    if uv_base==(-1, -1):
        unpack_uv_old(uv_, count)
        print('uvcount is  ' + str(count) +' uv_base is ' + str(uv_base))
    else:
        uv_base = uv_base or (0, 1)
        for _ in range(count):
            for uv_convert in uv_:
                uv_convert[0] = uv_convert[0] * 2 - uv_base[0]
                uv_convert[1] = uv_convert[1] * 2 - uv_base[1]
                #uv_convert[0] = uv_convert[0]
                #uv_convert[1] = uv_convert[1]

def unpack_uv_old(uv_, count):
    '''
    increases x,y value 2 times per side and offset by y(vertically)
    '''
    for _ in range(count):
        for uv_convert in uv_:
            uv_convert[0] *= 2
            uv_convert[1] = uv_convert[1] * 2 - 1
            
def pack_uv(uv_, count, uv_base=None):
    '''
    decreases x,y value 2 times per side and offset by y(vertically)
    '''
    
    if uv_base == (-1, -1) or uv_base is None:
        uv_base = (0, 1)
    for _ in range(count):
        for uv_convert in uv_:
            uv_convert[0] = uv_base[0]/2 + uv_convert[0]/2
            uv_convert[1] = uv_base[1]/2 + uv_convert[1]/2

def calculate_unique_component(ei_, comp):
    '''
    calculates unique component using base, strength and dexterity components
    '''
    temp = [0, 0, 0]

    for xyz in range(3):
        temp[xyz] = (ei_.center[comp-1][xyz] + \
            ei_.center[comp-2][xyz] - \
            ei_.center[comp-3][xyz])
    ei_.center[comp] = tuple(temp)


    for xyz in range(3):
        temp[xyz] = (ei_.fmin[comp-1][xyz] + \
            ei_.fmin[comp-2][xyz] - \
            ei_.fmin[comp-3][xyz])
    ei_.fmin[comp] = tuple(temp)

    for xyz in range(3):
        temp[xyz] = (ei_.fmax[comp-1][xyz] + \
            ei_.fmax[comp-2][xyz] - \
            ei_.fmax[comp-3][xyz])
    ei_.fmax[comp] = tuple(temp)

    ei_.radius[comp] = (ei_.radius[comp-1] + ei_.radius[comp-2] - ei_.radius[comp-3])

    for i in range(len(ei_.verts[0])):
        for xyz in range(3):
            temp[xyz] = (ei_.verts[comp-1][i][xyz] + \
                ei_.verts[comp-2][i][xyz] - \
                ei_.verts[comp-3][i][xyz])
        ei_.verts[comp].append(tuple(temp))

def md5(fname):
    hash_md5 = hashlib.md5()
    with open(fname, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def read_x(file):
    return unpack('h', file.read(2))[0]

def read_xy(file, data_type = 'float'):
    res = [0,0]
    for xy in range(2):
        if data_type == 'float':
            res[xy] = unpack('f', file.read(4))[0]
        elif data_type == 'short':
            res[xy] = unpack('h', file.read(2))[0]
    return tuple(res)

def write_xy(file, vec, data_type = 'f'):
    for xy in range(2):
        file.write(pack(data_type, vec[xy]))

def read_xyz(file):
    res = [0,0,0]
    for xyz in range(3):
        res[xyz] = unpack('f', file.read(4))[0]
    return tuple(res)

def write_xyz(file, vec):
    for xyz in range(3):
        file.write(pack('f', vec[xyz]))

def read_xyzw(file):
    res = [0,0,0,0]
    for xyzw in range(4):
        res[xyzw] = unpack('f', file.read(4))[0]
    return tuple(res)

def write_xyzw(file, vec):
    for xyzw in range(4):
        file.write(pack('f', vec[xyzw]))