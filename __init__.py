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

bl_info = {
    'name': 'EI figer',
    'author': 'Konstvest/LostSoul/Asbest',
    'version': (5, 6),
    'blender': (3, 0, 0),
    'location': '',
    'description': 'Addon for import/export models and animations from Evil Islands game to Blender',
    'wiki_url': '',
    'tracker_url': 'https://github.com/konstvest/ei_figer',
    'category': 'Import-Export'}

from . UI_panel import *
from . operators import *
from . properties import register_props, unregister_props
from bpy.utils import register_class
from bpy.utils import unregister_class


bl_panels = (
IMPORT_EXPORT_PT_PANEL,
OPERATOR_PT_PANEL,
OPERATORMASS_PT_PANEL,
ANIMATION_PT_PANEL
)

bl_operators = (
CChooseResFile,
CAddMorphComp_OP_Operator,
CAddMorphCompNamed_OP_Operator,
CAddAllMorphComp_OP_Operator,
CAutoFillMorphNew_OP_Operator,
CFixPos_OP_Operator,
CAutoFillMorphScaledOnly_OP_Operator,
CImport_OP_operator,
CAnimation_OP_import,
CAnimation_OP_Export,
CExport_OP_operator,
CAutoFillMorph_OP_Operator,
CAnimation_OP_shapekey

)

def register():    
    for panel in bl_panels:
        print ('reg panel: ' + str(panel))
        register_class(panel)
    for oper in bl_operators:
        print('reg operator: ' + str(oper))
        register_class(oper)

    register_props()
    
def unregister():
    for panel in bl_panels:
        unregister_class(panel)
    for oper in bl_operators:
        unregister_class(oper)

    unregister_props()

if __name__ == '__main__':
    register()
