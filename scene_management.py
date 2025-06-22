# Copyright (c) 2022 konstvest
import bpy

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
from .links import CLink
from .animation import CAnimation
from .figure import CFigure
from .bone import CBone


class CAnimations():
    def __init__(self, anm_list):
        self.anm_list: list[CAnimation] = anm_list

    def __repr__(self):
        length = len(self.anm_list)
        postfix = "..." if length > 10 else ""
        return f"CAnimations len={length} {self.anm_list[:10]} {postfix}"

    def __iter__(self):
        return iter(self.anm_list)

    def __getitem__(self, index):
        return self.anm_list[index]

    def __len__(self):
        return len(self.anm_list)

    def __contains__(self, item):
        return item in self.anm_list

    def reset(self):
        self.anm_list = []

    def __values__(self):
        return self.anm_list

    def get_animation(self, part_name: str):
        for anm in self.anm_list:
            if part_name.lower() == anm.name.lower():
                return anm
        return None


class CModel():
    morph_names = [
        'base',  # 0
        'str',  # 1
        'dex',  # 2
        'unique',  # 3
        'base(scaled)',  # 4
        'str(scaled)',  # 5
        'dex(scaled)',  # 6
        'unique(scaled)',  # 7
        # 'testUnit'          #8
    ]

    morph_prefixes = [
        '',
        's~',
        'd~',
        'u~',
        'b~',
        'p~',
        'g~',
        'c~',
    ]

    def __init__(self):
        self.reset()
        self.name = ''
        self.morph_comp = {
            0: ''
            , 1: 's~'  # str
            , 2: 'd~'  # dex
            , 3: 'u~'  # unique
            , 4: 'b~'  # big (scaled basis)
            , 5: 'p~'  # power (scaled str)
            , 6: 'g~'  # growth (scaled dex)
            , 7: 'c~'  # common (scaled unique)
            # ,8: 'T~' #test unit
        }

        self.morph_collection = [
            'base',  # 0
            'str',  # 1
            'dex',  # 2
            'unique',  # 3
            'base(scaled)',  # 4
            'str(scaled)',  # 5
            'dex(scaled)',  # 6
            'unique(scaled)',  # 7
            # 'testUnit'          #8
        ]

        self.mesh_list: list[CFigure] = list()
        self.pos_list: list[CBone] = list()

    def reset(self, type: str = 'all'):
        if type == 'fig' or type == 'all':
            self.mesh_list: list[CFigure] = list()
            self.pos_list: list[CBone] = list()

    def is_morph_name(self, name: str):
        for morph in self.morph_comp.values():
            if not morph:
                continue
            if name.startswith(morph):
                return True
        return False
