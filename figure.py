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

import bpy
import numpy as np

from . import utils as fig_utils


class CFigureHeader:
    fields = [
        "vertex_count",
        "normal_count",
        "texcoord_count",
        "index_count",
        "vertex_component_count",
        "morph_component_count",
        "unknown",
        "group",
        "texture_number",
    ]

    def __init__(self):
        self.vertex_count = 0
        self.normal_count = 0
        self.texcoord_count = 0
        self.index_count = 0
        self.vertex_component_count = 0
        self.morph_component_count = 0
        self.unknown = 0
        self.group = 0
        self.texture_number = 0

    def get_member_names(self):
        # members = filter(lambda field: field.startswith('m_'), dir(self))
        # return list(members)
        return self.fields

    def get_array(self):
        array = [self[i] for i in range(9)]
        return array

    def __getitem__(self, key):
        if isinstance(key, int):
            member = self.get_member_names()[key]
            return getattr(self, member)
        return getattr(self, key)

    def __setitem__(self, key, value):
        if isinstance(key, int):
            member = self.get_member_names()[key]
            setattr(self, member, value)
        else:
            setattr(self, key, value)

    def __str__(self):
        parts = []
        fields = self.get_member_names()
        for field in fields:
            value = self[field]
            parts.append("%s: %s" % (field, value))
        parts.insert(4, '\n===>')
        text = ' - '.join(parts)
        text = '<HEADER: %s >' % text
        return text


class CFigure(object):
    '''
    3D model with morphing components
    '''

    def __init__(self):
        self.name = ''
        self.signature = ''
        self.header = CFigureHeader()
        self.center = []  # (0.0, 0.0, 0.0) for _ in range(8)
        self.fmin = []  # (0.0, 0.0, 0.0) for _ in range(8)
        self.fmax = []  # (0.0, 0.0, 0.0) for _ in range(8)
        self.radius = []  # 0.0 for _ in range(8)
        # [main], [strength], [dexterity], [unique] and scaled once
        self.verts = [[], [], [], [], [], [], [], []]
        self.normals = []
        # texture coordinates
        self.t_coords = []
        # indicies
        self.indicies = []
        # vertex components
        self.v_c = []
        self.m_c = []
        self.morph_count = 8

    def __eq__(self, other):
        if not isinstance(other, CFigure):
            # don't attempt to compare against unrelated types
            return NotImplemented

        return NotImplemented

        is_equal = header == other.header and self.center == other.center and self.fmin == other.fmin
        is_equal = is_equal and self.fmax == other.fmax and self.radius == other.radius
        is_equal = is_equal and self.indicies == other.indicies and self.v_c == other.v_c
        # TODO: set precision for compare points
        is_equal = is_equal and self.verts == other.verts and self.normals == other.normals
        is_equal = is_equal and self.t_coords == other.t_coords

        return is_equal

    @staticmethod
    def is_old_fig6(signature):
        is_old_figure = not signature.startswith('FIG')
        return is_old_figure

    @staticmethod
    def get_morph_count(signature, is_etherlord=False):
        if is_etherlord:
            return 1
        if signature == 'FIG8':
            return 8
        elif signature == 'FIG6':
            return 6
        elif signature == 'FIG4':
            return 4
        else:
            # old fig6
            return 6

    def read_bounding_volume(self, parser: fig_utils.CByteReader):
        for _ in range(self.morph_count):
            self.center.append(parser.read('fff'))
        for _ in range(self.morph_count):
            self.fmin.append(parser.read('fff'))
        for _ in range(self.morph_count):
            self.fmax.append(parser.read('fff'))
        for _ in range(self.morph_count):
            self.radius.append(parser.read('f'))

    def read_fig(self, name, raw_data: bytearray):
        self.name = name
        parser = fig_utils.CByteReader(raw_data)
        print('Name: ' + name)
        signature = parser.read('ssss').decode()
        self.signature = signature
        print('signature', signature)
        if signature != 'FIG8':
            print(self.name + ' has not FIG8 figure signature: %s (0x%s)' % (signature, signature.encode().hex()))
        is_etherlord = bpy.context.scene.ether
        self.morph_count = self.get_morph_count(signature, is_etherlord)

        if self.is_old_fig6(signature):
            # old figure has no signature, so reset
            parser.reset()
            return read_old_fig6(self, parser)

        print(self.name + ' have morph_count of ' + str(self.morph_count))
        header = self.header
        for i in range(9):
            header[i] = parser.read('L')
        self.read_bounding_volume(parser)
        # VERTICES
        n_vertex_blocks = header.vertex_count
        # block is XXXX * morph_count, YYYY * morph_count, ZZZZ * morph_count
        # 3 coords (XYZ) * morph_count * 4 coords (XXXX)
        n_floats_per_block = 3 * self.morph_count * 4
        vertex_data = parser.read('%uf' % (n_vertex_blocks * n_floats_per_block))
        vertices = np.array(vertex_data).reshape((n_vertex_blocks, 3, self.morph_count, 4))
        # reorder axes. black magic?
        vertices = vertices.transpose(2, 0, 3, 1)
        # XYZ * 4 * n_vertex blocks (for morph 1), same for morph 2, etc...
        vertices = vertices.reshape((self.morph_count, n_vertex_blocks * 4, 3))
        self.verts = vertices
        # NORMALS
        n_normal4_blocks = header.normal_count
        n_normals = n_normal4_blocks * 4
        # useless for mesh creation, but may need to be validated
        normal_data = parser.read('%uf' % (n_normals * 4))
        self.normals = np.array(normal_data).reshape(n_normals, 4)
        # TEXTURE COORDS
        n_texcoords = header.texcoord_count
        texcoords_data = parser.read('%uf' % (n_texcoords * 2))
        texcoords = np.array(texcoords_data).reshape(n_texcoords, 2)
        # unpack
        convert_count, uv_base = fig_utils.get_uv_params(self.name)
        packed_uvs = fig_utils.unpack_uv_np(texcoords, convert_count, uv_base)
        self.t_coords = packed_uvs
        # INDICES
        n_indices = header.index_count
        self.indicies = np.array(parser.read('%uH' % n_indices))
        # VERTEX COMPONENTS
        n_components = header.vertex_component_count
        self.v_c = np.array(parser.read('%uH' % (n_components * 3))).reshape((n_components, 3))
        # MORPHING COMPONENTS
        # useless for mesh creation, but may need to be validated
        n_morphs = header.morph_component_count
        # parser.read('%uH' % (n_morphs * 2))
        self.m_c = np.array(parser.read('%uH' % (n_morphs * 2))).reshape((n_morphs, 2))
        if parser.is_EOF():
            print('EOF reached')
            return 0
        return 1

    def write_fig(self):
        header = self.header
        if len(self.normals) != header.normal_count * 4:  # normal count * block_size(4)
            print('normals count corrupted')
        if len(self.t_coords) != header.texcoord_count:
            print('texture coordinates count corrupted')
        if len(self.indicies) != header.index_count:
            print('indices count corrupted')
        if len(self.m_c) != header.morph_component_count:
            print('morph components count corrupted')
        if len(self.center) != 8 or len(self.fmin) != 8 or len(self.fmax) != 8 or len(self.center) != 8:
            print('aux data components count corrupted')

        pack = struct.pack
        raw_data = pack('4s', b'FIG8')
        # header
        assert (len(header.get_array()) == 9)
        raw_data += pack('9L', *header.get_array())
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
        n_vertex_blocks = header[0]
        # [xyz xyz xyz xyz] * n_vertices4 * n_morph_count
        verts = np.concatenate(self.verts)
        # [XXXX * morph_count, YYYY * morph_count, ZZZZ * morph_count] * n_vertices4
        assert verts.dtype == np.float32
        vertex_data = verts.reshape((self.morph_count, n_vertex_blocks, 4, 3)).transpose(1, 3, 0, 2).tobytes()
        raw_data += vertex_data
        # normals
        n_normal4_blocks = header.normal_count
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

    def fill_vertices(self):
        for i in range(1, 8):
            self.verts[i] = self.verts[0]

    def fill_bounding_volume(self):
        for i in range(1, 8):
            self.fmin.append(self.fmin[0])
            self.fmax.append(self.fmax[0])
            self.center.append(self.center[0])
            self.radius.append(self.radius[0])

    def generate_m_c(self):
        n_morph_components = self.header.morph_component_count
        self.m_c = np.repeat(np.arange(n_morph_components, dtype=np.uint16), 2).reshape(n_morph_components, 2)


def read_old_fig6(self: CFigure, parser: fig_utils.CByteReader):
    print(self.name + ' have morph_count of ' + str(self.morph_count))
    header = self.header
    header.group = parser.read('L')
    header.texture_number = parser.read('L')
    self.read_bounding_volume(parser)
    # VERTICES
    header.vertex_count = parser.read('L')
    n_vertex_blocks = header.vertex_count
    # block is XXXX * morph_count, YYYY * morph_count, ZZZZ * morph_count
    # 3 coords (XYZ) * morph_count * 4 coords (XXXX)
    n_floats_per_block = 3 * self.morph_count * 4
    vertex_data = parser.read('%uf' % (n_vertex_blocks * n_floats_per_block))
    vertices = np.array(vertex_data).reshape((n_vertex_blocks, 3, self.morph_count, 4))
    # reorder axes. black magic?
    vertices = vertices.transpose(2, 0, 3, 1)
    # XYZ * 4 * n_vertex blocks (for morph 1), same for morph 2, etc...
    vertices = vertices.reshape(self.morph_count, n_vertex_blocks * 4, 3)
    self.verts = vertices
    # NORMALS
    header.normal_count = parser.read('L')
    n_normal4_blocks = header.normal_count
    n_normals = n_normal4_blocks * 4
    # useless for mesh creation, but may need to be validated
    normal_data = parser.read('%uf' % (n_normals * 4))
    self.normals = np.array(normal_data).reshape(n_normals, 4)
    # TEXTURE COORDS
    header.texcoord_count = parser.read('L')
    n_texcoords = header.texcoord_count
    texcoords_data = parser.read('%uf' % (n_texcoords * 2))
    texcoords = np.array(texcoords_data).reshape(n_texcoords, 2)
    # unpack
    convert_count, uv_base = fig_utils.get_uv_params(self.name)
    packed_uvs = fig_utils.unpack_uv_np(texcoords, convert_count, uv_base)
    self.t_coords = packed_uvs
    # FACES - doesn't exist in FIGN (and unnecessary anyway)
    n_faces = parser.read('L')
    # skip 52 byte per face
    parser.read('%us' % (n_faces * 52))
    # Should be INDICES in FIGN, but instead we have
    # VERTEX COMPONENTS
    header.vertex_component_count = parser.read('L')
    n_components = header.vertex_component_count
    # 3 uint16 per component
    self.v_c = np.array(parser.read('%uH' % (n_components * 3))).reshape((n_components, 3))
    ### MORPHING COMPONENTS
    # useless for mesh creation, but may need to be validated
    header.morph_component_count = parser.read('L')
    n_morphs = header.morph_component_count
    # 2 uint16 per component
    self.m_c = np.array(parser.read('%uH' % (n_morphs * 2))).reshape((n_morphs, 2))
    # INDICES
    header.index_count = parser.read('L')
    n_indices = header.index_count
    # 1 uint16 per index
    self.indicies = np.array(parser.read('%uH' % n_indices))
    if parser.is_EOF():
        print('EOF reached')
        return 0
    return 1
