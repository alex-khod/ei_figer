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
import os
import bpy
import numpy as np
from struct import pack, unpack
from mathutils import Quaternion
from .utils import read_xyzw, write_xyzw, read_xyz, write_xyz, CByteReader


class CAnimation(object):
    '''
    container of EI figure animation frames
    '''

    def __init__(self):
        self.name = ''
        self.rotations = []  # rotation in w,x,y,z for each frame
        self.abs_rotation: list[Quaternion] = []
        self.translations = []
        self.scalings = []
        self.morphations = []
        self.num_morph_verts = 0
        self.frameinfo = []

    def __repr__(self):
        # return f"CAnimation: name={self.name} at {id(self)}"
        return f"CAnimation: name={self.name}"

    def read_anm(self, name, raw_data: bytearray):
        """
        Reads animation data from byte array (from .res file)
        """
        self.name = name
        parser = CByteReader(raw_data)
        print('anm_name', name)
        # rotations
        rot_count = parser.read('L')
        print('rot_count', rot_count)
        rotations = [Quaternion(parser.read('ffff')) for _ in range(rot_count)]
        self.rotations = rotations

        trans_count = parser.read('L')
        print('trans_count', trans_count)
        translations = [(parser.read('fff')) for _ in range(trans_count)]
        self.translations = translations

        bEtherlord = bpy.context.scene.ether
        if bEtherlord:
            scale_count = parser.read('L')
            print('scale_count', scale_count)
            scalings = [parser.read('fff') for _ in range(scale_count)]
            self.scalings = scalings

        morph_frame_count = parser.read('L')
        morph_vert_count = parser.read('L')
        self.num_morph_verts = morph_vert_count

        print('morph frames:', morph_frame_count, 'morph verts:', morph_vert_count)

        morphanim_data = parser.read('%df' % (morph_frame_count * morph_vert_count * 3))
        self.morphations = np.array(morphanim_data).reshape((morph_frame_count, morph_vert_count, 3))

        if parser.is_EOF():
            # print('EOF reached (morphs)')
            return 0
        print('Warning: no EOF!')
        return 1

    def write_anm(self):
        raw_data = b''
        raw_data += pack('L', len(self.rotations))
        for rot in self.rotations:
            raw_data += pack('%uf' % len(rot), *rot)
        # translations
        raw_data += pack('L', len(self.translations))
        for trans in self.translations:
            raw_data += pack('%uf' % len(trans), *trans)
        # morphations
        # n_frames
        raw_data += pack('L', len(self.morphations))
        n_vertices_per_frame = len(self.morphations[0]) if len(self.morphations) else 0
        raw_data += pack('L', n_vertices_per_frame)

        for frame in self.morphations:
            assert (len(frame) == n_vertices_per_frame)
            raw_data += frame.tobytes()

        return raw_data
