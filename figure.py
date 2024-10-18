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
from . import utils as fig_utils

import numpy as np

class CFigure(object):
    '''
    3D model with morphing components
    '''
    def __init__(self):
        self.name = ''
# header:
# vertex_count
# normal_count
# texcoord_count
# index_count
# vertex_component_count
# morph_component_count
# unknown
# group
# texture_number
        self.header = [0 for _ in range(9)]
        self.center = [] #(0.0, 0.0, 0.0) for _ in range(8)
        self.fmin = [] #(0.0, 0.0, 0.0) for _ in range(8)
        self.fmax = [] #(0.0, 0.0, 0.0) for _ in range(8)
        self.radius = [] #0.0 for _ in range(8)
        # [main], [strength], [dexterity], [unique] and scaled once
        self.verts = [[], [], [], [], [], [], [], []]
        self.normals = []
        #texture coordinates
        self.t_coords = []
        #indicies
        self.indicies = []
        #vertex components
        self.v_c = []
        self.m_c = []
        self.morph_count = 8

    def __eq__(self, other):
        if not isinstance(other, CFigure):
            # don't attempt to compare against unrelated types
            return NotImplemented

        return NotImplemented

        is_equal = self.header == other.header and self.center == other.center and self.fmin == other.fmin
        is_equal = is_equal and self.fmax == other.fmax and self.radius == other.radius
        is_equal = is_equal and self.indicies == other.indicies and self.v_c == other.v_c
        #TODO: set precision for compare points
        is_equal = is_equal and self.verts == other.verts and self.normals == other.normals
        is_equal = is_equal and self.t_coords == other.t_coords

        return is_equal

    def read_fig(self, name, raw_data : bytearray):
        self.name = name
        parser = fig_utils.CByteReader(raw_data)
        print('Name: ' + name)
        signature = parser.read('ssss').decode()
        print('signature is ' + str(signature))
        if signature != 'FIG8':
            print(self.name + ' has not FIG8 figure signature: ' + signature)
        if signature == 'FIG8':
            self.morph_count = 8
        elif signature == 'FIG6':
            self.morph_count = 6
        elif signature == 'FIG4':
            self.morph_count = 4
        else:    
            self.morph_count = 1

        print(self.name + ' have morph_count is ' + str(self.morph_count))

        for i in range(9):
            self.header[i] = parser.read('L')
#            print('self.header[i] is ' + str(self.header[i]))
        # Center
        for _ in range(self.morph_count):
            Center = self.center.append(parser.read('fff'))
        # MIN
        for _ in range(self.morph_count):
            self.fmin.append(parser.read('fff'))
#        print('self.fmin is ' + str(self.fmin))
        # MAX
        for _ in range(self.morph_count):
            self.fmax.append(parser.read('fff'))
#        print('self.fmax is ' + str(self.fmax))
        # Radius
        for _ in range(self.morph_count):
            self.radius.append(parser.read('f'))
#        print('self.radius is ' + str(self.radius))
        # VERTICES
        print(self.header)
        n_vertex_blocks = self.header[0]
        # block is XXXX * morph_count, YYYY * morph_count, ZZZZ * morph_count
        # 3 coords (XYZ) * morph_count * 4 coords (XXXX)
        n_floats_per_block = 3 * self.morph_count * 4
        vertex_data = parser.read('%uf' % (n_vertex_blocks * n_floats_per_block))
        vertices = np.array(vertex_data).reshape(n_vertex_blocks, 3, self.morph_count, 4)
        # reorder axes. black magic?
        vertices = vertices.transpose(2, 0, 3, 1)
        # XYZ * 4 * n_vertex blocks (for morph 1), same for morph 2, etc...
        vertices = vertices.reshape(self.morph_count, n_vertex_blocks * 4, 3)
        self.verts = vertices
        # NORMALS
        n_normal4_blocks = self.header[1]
        n_normals = n_normal4_blocks * 4
        # useless for mesh creation, but may need to be validated
        normal_data = parser.read('%uf' % (n_normals * 4))
        self.normals = np.array(normal_data).reshape(n_normals, 4)
        # TEXTURE COORDS
        n_texcoords = self.header[2]
        texcoords_data = parser.read('%uf' % (n_texcoords * 2))
        texcoords = np.array(texcoords_data).reshape(n_texcoords, 2)
        # unpack
        convert_count, uv_base = fig_utils.get_uv_params(self.name)
        packed_uvs = fig_utils.unpack_uv_np(texcoords, convert_count, uv_base)
        self.t_coords = packed_uvs
        # INDICES
        n_indicies = self.header[3]
        self.indicies = np.array(parser.read('%uH' % n_indicies))
        # VERTEX COMPONENTS
        n_components = self.header[4]
        self.v_c = np.array(parser.read('%uH' % (n_components * 3))).reshape((n_components, 3))
        # MORPHING COMPONENTS
        # useless for mesh creation, but may need to be validated
        n_morphs = self.header[5]
        # parser.read('%uH' % (n_morphs * 2))
        self.m_c = np.array(parser.read('%uH' % (n_morphs * 2))).reshape((n_morphs, 2))
        if parser.is_EOF():
            print('EOF reached')
            return 0
        return 1

    def write_fig(self):
        if len(self.normals) != self.header[1]*4: #normal count * block_size(4)
            print('normals count corrupted')
        if len(self.t_coords) != self.header[2]:
            print('texture coordinates count corrupted')
        if len(self.indicies) != self.header[3]:
            print('indices count corrupted')
        if len(self.m_c) != self.header[5]:
            print('morph components count corrupted')
        if len(self.center) != 8 or len(self.fmin) != 8 or len(self.fmax) != 8 or len(self.center) != 8:
            print('aux data components count corrupted')

        pack = struct.pack
        raw_data = pack('4s', b'FIG8')
        # header
        assert(len(self.header) == 9)
        raw_data += pack('9L', *self.header)
        # center
        for v_c in self.center:
            raw_data += pack('%sf' % len(v_c), *v_c)
        # min
        for v_c in self.fmin:
            raw_data += pack('%sf' % len(v_c), *v_c)
        # max
        for v_c in self.fmax:
            raw_data += pack('%sf' % len(v_c), *v_c)
        # radius
        for rad in self.radius:
            raw_data += pack('f', rad)
        # verts
        n_vertex_blocks = self.header[0]
        # [xyz xyz xyz xyz] * n_vertices4 * n_morph_count
        verts = np.concatenate(self.verts)
        # [XXXX * morph_count, YYYY * morph_count, ZZZZ * morph_count] * n_vertices4
        assert verts.dtype == np.float32
        vertex_data = verts.reshape(self.morph_count, n_vertex_blocks, 4, 3).transpose(1, 3, 0, 2).tobytes()
        raw_data += vertex_data
        # normals
        n_normal4_blocks = self.header[1]
        assert self.normals.dtype == np.float32
        raw_data += self.normals.reshape(n_normal4_blocks, 4, 4).transpose(0, 2, 1).tobytes()
        assert self.t_coords.dtype == np.float32
        raw_data += self.t_coords.tobytes()
        # indicies
        assert self.indicies.dtype == np.uint16
        raw_data += self.indicies.tobytes()
        # raw_data += pack('%uh' % len(self.indicies), *self.indicies)
        # vertex components
        assert self.v_c.dtype == np.uint16
        raw_data += self.v_c.tobytes()
        # raw_data += pack('%uh' % len(vertex_components), *vertex_components)
        # self.m_c = np.array([], dtype=np.uint16)

        assert self.m_c.dtype == np.uint16
        raw_data += self.m_c.tobytes()
        # morph_components = [co for m_c in self.m_c for co in m_c]
        # raw_data += pack('%sh' % len(morph_components), *morph_components)
        return raw_data
    
    def fillVertices(self):
        for i in range(1, 8):
            self.verts[i] = self.verts[0]

    def fillAux(self):
        for i in range(1, 8):
            self.fmin.append(self.fmin[0])
            self.fmax.append(self.fmax[0])
            self.center.append(self.center[0])
            self.radius.append(self.radius[0])


    def generate_m_c(self):
        n_morph_components = self.header[5]
        self.m_c = np.repeat(np.arange(n_morph_components, dtype=np.uint16), 2).reshape(n_morph_components, 2)
