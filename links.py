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
import struct
from .utils import CByteReader


class CLink:
    def __init__(self):
        # [child] = parent graph
        self.links = dict()

    def __str__(self):
        return "<Clink: %s>" % self.links.__str__()

    def get_roots(self):
        roots = [k for k, v in  filter(lambda k, v: v is None, self.links.items())]
        return roots

    def read_lnk(self, raw_data: bytearray):
        parser = CByteReader(raw_data)

        def read_fixed_string():
            part_len = parser.read('i')
            if part_len == 0:
                return None
            part = parser.read(part_len * 's').decode().rstrip('\x00')
            return part

        link_count = parser.read('i')
        for _ in range(link_count):
            parent = read_fixed_string()
            child = read_fixed_string()
            self.links[parent] = child
        print(self.links)
        if parser.is_EOF():
            # print('EOF reached')
            return 0
        return 1

    def write_lnk(self):
        pack = struct.pack
        raw_data = b''
        raw_data += pack('i', len(self.links.keys()))

        def write_fixed_string(_str: str):
            encoded = _str.encode() + b'\x00'
            data = b'' + pack('i', len(encoded))
            data += pack('%us' % len(encoded), encoded)
            return data

        for parent, child in self.links.items():
            raw_data += write_fixed_string(parent)
            if child is None:
                raw_data += pack('i', 0)
            else:
                raw_data += write_fixed_string(child)

        print(raw_data)

        return raw_data

