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
import importlib
from bpy.utils import register_class
from bpy.utils import unregister_class

from . import UI_panel
from . import animation
from . import figure
from . import operators
from . import scene_management
# for reloading
from . import scene_utils
from .properties import register_props, unregister_props

bl_info = {
    'name': 'EI figer',
    'author': 'Konstvest/LostSoul/Asbestos',
    'version': (5, 9),
    'blender': (3, 1, 0),
    'location': '',
    'description': 'Addon for import/export models and animations from Evil Islands game to Blender',
    'wiki_url': '',
    'tracker_url': 'https://github.com/konstvest/ei_figer',
    'category': 'Import-Export'}

bl_panels = (
    UI_panel.IMPORT_EXPORT_PT_PANEL,
    UI_panel.OPERATOR_PT_PANEL,
    UI_panel.OPERATORMASS_PT_PANEL,
    UI_panel.ANIMATION_PT_PANEL
)

bl_operators = (
    operators.CChooseResFile,
    operators.CSelectResFileIndex,
    operators.CAddMorphComp_OP_Operator,
    operators.CAddMorphCompNamed_OP_Operator,
    operators.CAddAllMorphComp_OP_Operator,
    operators.CAutoFillMorphNew_OP_Operator,
    operators.CFixPos_OP_Operator,
    operators.CAutoFillMorphScaledOnly_OP_Operator,
    operators.CImport_OP_operator,
    operators.CAnimation_OP_import,
    operators.CAnimation_OP_Export,
    operators.CAnimation_OP_BakeTransform,
    operators.CExport_OP_operator,
    operators.CAutoFillMorph_OP_Operator,
    operators.CAnimation_OP_shapekey,
    operators.CClear_OP_operator,
    operators.CRenameDropPostfix_OP_operator,
    operators.CAnimation_OP_UE4_Toolchain,
    operators.CDebugTestOperator,
)

bl_menus = (
    (bpy.types.OUTLINER_MT_collection, UI_panel.outliner_mt_collection),
    (bpy.types.OUTLINER_MT_object, UI_panel.outliner_mt_object),
)


def add_context_menu(self, operator_class):
    self.layout.menu(operator_class.bl_idname)


def reload_modules():
    importlib.reload(properties)
    importlib.reload(UI_panel)
    importlib.reload(operators)

    importlib.reload(scene_utils)
    importlib.reload(scene_management)
    importlib.reload(animation)
    importlib.reload(figure)


def register():
    print("Register")

    for panel in bl_panels:
        print('reg panel: ' + str(panel))
        register_class(panel)
    for oper in bl_operators:
        print('reg operator: ' + str(oper))
        register_class(oper)
    for menu, menu_draw in bl_menus:
        menu.append(menu_draw)

    register_props()


def unregister():
    reload_modules()
    for panel in bl_panels:
        unregister_class(panel)
    for oper in bl_operators:
        unregister_class(oper)
    for menu, menu_draw in bl_menus:
        print("register menu", menu, menu_draw)
        menu.append(menu_draw)

    unregister_props()


if __name__ == '__main__':
    register()
