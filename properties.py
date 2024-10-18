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
import bpy
from . scene_utils import calculate_mesh
from . scene_management import CModel

def register_props():
    scene = bpy.types.Scene

    scene.res_file_index = bpy.props.IntProperty(
        name='ResFileIdx',
        default=0,
        description='# of res file to use'
    )

    scene.res_file = bpy.props.StringProperty(
        name='Current Res',
        default='?.res',
        description='*.res file containing models, figures, animations. Usually Figures.res'
    )

    for i in range(0, 3):
        prop = bpy.props.StringProperty(
            name='Res %d' % (i + 1),
            default='figures.res',
            description='*.res file containing models, figures, animations. Usually Figures.res'
        )
        setattr(scene, "res_file_buffer%d" % i,  prop)

    scene.figmodel_name = bpy.props.StringProperty(
        name='Name',
        default='',
        description='Write Model/Figure name to Import/Export'
    )

    scene.animation_name = bpy.props.StringProperty(
        name='Name',
        default='',
        description='Write Animation Name for Import/Export Model/Figure animation'
    )
    
    scene.scaled = bpy.props.FloatProperty(
        name='scaled',
        default=3.0,
        step=10,
        description='Scale of scaled morph'
    )
    
    scene.s_s_x = bpy.props.FloatProperty(
        name='Sx',
        default=1.0,
        step=10,
        description='Scale X of Strenght'
    )
    scene.s_s_y = bpy.props.FloatProperty(
        name='Sy',
        default=1.0,
        step=10,
        description='Scale Y of Strenght'
    )
    scene.s_s_z = bpy.props.FloatProperty(
        name='Sz',
        default=1.0,
        step=10,
        description='Scale Z of Strenght'
    )

    scene.s_d_x = bpy.props.FloatProperty(
        name='Dx',
        default=1.0,
        step=10,
        description='Scale X of Dexterity'
    )
    scene.s_d_y = bpy.props.FloatProperty(
        name='Dy',
        default=1.0,
        step=10,
        description='Scale Y of Dexterity'
    )
    scene.s_d_z = bpy.props.FloatProperty(
        name='Dz',
        default=1.0,
        step=10,
        description='Scale Z of Dexterity'
    )

    scene.s_u_x = bpy.props.FloatProperty(
        name='Ux',
        default=1.0,
        step=10,
        description='Scale X of Unique'
    )
    scene.s_u_y = bpy.props.FloatProperty(
        name='Uy',
        default=1.0,
        step=10,
        description='Scale Y of Unique'
    )
    scene.s_u_z = bpy.props.FloatProperty(
        name='Uz',
        default=1.0,
        step=10,
        description='Scale Z of Unique'
    )

    scene.morph_comp = bpy.props.EnumProperty(
        items=[
            ('s~', 'str (s~)', 'Strength component', 1),
            ('d~', 'dex (d~)', 'Dexterity component', 2),
            ('u~', 'unique (u~)',
             'Mean combination of Strength & Dexterity components in one object', 3),
            ('b~', 'base(scaled) (b~)', 'Scaled base figure', 4),
            ('p~', 'str(scaled) (p~)', 'Scaled strength component', 5),
            ('g~', 'dex(scaled) (g~)', 'Scaled dexterity component', 6),
            ('c~', 'unique(scaled) (c~)', 'Scaled Unique component', 7)
        ], 
        name='', 
        description='Select morphing component to copy', 
        default='s~'
    )

    scene.figcopy_name = bpy.props.StringProperty(
        name='Name',
        default='',
        description='Name of figure you want to copy'
    )
    scene.figcopy_parent = bpy.props.StringProperty(
        name='Parent',
        default='',
        description='Parent of figure you want to copy'
    )

    scene.mesh_mask = bpy.props.StringProperty(
        name='Mesh mask',
        default="",
        description="Partial import/export of a model. Needs full base collection to be present in a scene.\n"
                    "Fill as comma-separated include list of meshes (include all meshes if empty).\n"
                    "Example: `head, body`\n"
                    "NOTE: More handily, use object RMB context menu in outliner (base collection only!)"
    )

    scene.mesh_str = bpy.props.FloatProperty(
        name='str',
        default=0.5,
        step=2,
        update=calculate_mesh
    )

    scene.mesh_dex = bpy.props.FloatProperty(
        name='dex',
        default=0.5,
        step=2,
        update=calculate_mesh
    )

    scene.mesh_height = bpy.props.FloatProperty(
        name='height',
        default=0.5,
        step=2,
        update=calculate_mesh
    )

    scene.auto_fix = bpy.props.BoolProperty(
        name='auto_fix',
        description='This option allows to triangulate model, and switch to object mode automatically before export.\n\
Can be useful if you get unexpected scaling, rotations or holes. It can decrease performance, use it at your own risk.',
        default=False
    )
    scene.auto_apply = bpy.props.BoolProperty(
        name='autofixandapply',
        description='This option allows to triangulate model and aplly modificators.\n\
Can be useful if you get unexpected scaling, rotations or holes. It can decrease performance, use it at your own risk.',
        default=False
    )
    scene.auto_replace = bpy.props.BoolProperty(
        name='Replace',
        description='Replace model in target collection',
        default=True
    )
    scene.morph1 = bpy.props.BoolProperty(
        name='str',
        description='Str collection',
        default=False
    )
    scene.morph2 = bpy.props.BoolProperty(
        name='dex',
        description='Dex collection',
        default=False
    )
    scene.morph3 = bpy.props.BoolProperty(
        name='uniq',
        description='Unique collection',
        default=False
    )
    scene.morph4 = bpy.props.BoolProperty(
        name='b(s)',
        description='Base scaled collection',
        default=False
    )
    scene.morph5 = bpy.props.BoolProperty(
        name='s(s)',
        description='Str scaled collection',
        default=False
    )
    scene.morph6 = bpy.props.BoolProperty(
        name='d(s)',
        description='Dex scaled collection',
        default=False
    )
    scene.morph7 = bpy.props.BoolProperty(
        name='u(s)',
        description='Unique scaled collection',
        default=False
    )
    scene.ether = bpy.props.BoolProperty(
        name='ether',
        description='For Etherlords FIG1 models and animation import.',
        default=False
    )
    scene.animsubfix = bpy.props.BoolProperty(
        name='animsubfix',
        description='To correct bug rotations.',
        default=False
    )
    scene.skeletal = bpy.props.BoolProperty(
        name='skeletal',
        description='For transfer anim from armature.',
        default=False
    )
    scene.is_animation_to_new_collection = bpy.props.BoolProperty(
        name='Import/export as new collection',
        description='Unchecked: import into base collection, checked: import into copy of base collection',
        default=False
    )
    scene.is_export_unique = bpy.props.BoolProperty(
        name='Export unique vertices/components',
        description='If checked, packs model more tightly, reducing mesh size by ~30%',
        default=True
    )
    scene.model = CModel()

def unregister_props():
    scene = bpy.types.Scene
    del scene.res_file
    for i in range(0, 3):
        delattr(scene, "res_file_buffer%d" % i)
    del scene.figmodel_name
    del scene.animation_name
    del scene.morph_comp

    del scene.mesh_str
    del scene.mesh_dex
    del scene.mesh_height

    del scene.is_animation_to_new_collection
    del scene.mesh_mask

    del scene.skeletal

    del scene.model