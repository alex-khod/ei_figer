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

from .resfile import ResFile
from . import scene_utils
from . import operators

from bpy.app import translations

_ = translations.pgettext


class EVIL_ISLANDS_PROPS(bpy.types.Panel):
    bl_label = "Evil Islands props"
    bl_idname = "EVIL_ISLANDS_PROPS"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "object"

    def draw(self, context):
        layout = self.layout
        obj = context.object

        layout.prop(obj, "imported_parent")
        layout.prop(obj, "imported_item_group")


class LIST_RES_MODELS(bpy.types.UIList):

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        if item:
            layout.prop(item, "name", text="", emboss=False, icon_value=icon)
            layout.operator('object.model_select', text="✓").model_name = item.name
            layout.operator('object.model_import', text='Import').model_name = item.name
            # layout.operator('object.model_export', text="Export").model_name = item.name
        else:
            layout.label(text="", translate=False, icon_value=icon)
        # if self.layout_type in {'DEFAULT', 'COMPACT'}:
        # # 'GRID' layout type should be as compact as possible (typically a single icon!).
        # elif self.layout_type == 'GRID':
        #     layout.alignment = 'CENTER'
        #     layout.label(text="", icon_value=icon)


class LIST_RES_ANIMATIONS(bpy.types.UIList):

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            if item:
                layout.prop(item, "name", text="", emboss=False, icon_value=icon)
                layout.operator('object.animation_select', text="✓").animation_name = item.name
                layout.operator('object.animation_import', text="Import").animation_name = item.name
                # layout.operator('object.animation_export')
            else:
                layout.label(text="", translate=False, icon_value=icon)
        # 'GRID' layout type should be as compact as possible (typically a single icon!).
        elif self.layout_type == 'GRID':
            layout.alignment = 'CENTER'
            layout.label(text="", icon_value=icon)


class IMPORT_EXPORT_PT_PANEL(bpy.types.Panel):
    bl_label = 'import-export'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'EI_Tools'

    def draw_header(self, context):
        layout = self.layout
        layout.label(text='', icon='PACKAGE')

    def draw(self, context):
        layout = self.layout
        layout.label(text="Current RES:")
        scene = context.scene
        layout.label(text=str(scene.res_file), icon='FILE_FOLDER')
        for index in range(0, 3):
            row = layout.row()
            elem = row.split(factor=0.8)
            elem.prop(scene, 'res_file_buffer%d' % index)
            elem.operator('object.choose_resfile', text='...').res_file_index = index
            elem.operator('object.select_resfile', text="✓").res_file_index = index
        # model list
        row = layout.row()
        icon = 'TRIA_DOWN' if scene.show_model_list else 'TRIA_RIGHT'
        row.prop(scene, 'show_model_list', icon=icon, icon_only=True)
        row.label(text="Models (.res)")
        if scene.show_model_list:
            layout.template_list("LIST_RES_MODELS", "", scene, "model_list", scene, "active_res_model")
        ###
        layout.prop(scene, 'figmodel_name')
        layout.prop(scene, 'mesh_mask')
        mesh_mask = scene.mesh_mask
        op_name = operators.CModelImport.get_name(mesh_mask)
        layout.prop(scene, 'item_container_set')
        op_import = layout.operator('object.model_import',text=op_name)
        op_import.model_name = context.scene.figmodel_name
        op_import.mesh_mask = mesh_mask
        # (scene.figmodel_name, mesh_mask)
        row = layout.split()
        row.prop(scene, 'auto_fix')
        row.prop(scene, 'is_etherlord')
        row.prop(scene, 'is_export_unique', text="compact")
        layout.prop(scene, 'is_ignore_without_morphs')
        row = layout.row()

        op_name = operators.CModelExport.get_name(mesh_mask)
        op_export = layout.operator('object.model_export', text=op_name)
        op_export.model_name = context.scene.figmodel_name
        op_export.mesh_mask = mesh_mask

        row = layout.row()
        row.operator('object.clear_scene', text='Clear scene')
        row.operator('object.repack_resfile')


class OPERATOR_PT_PANEL(bpy.types.Panel):
    bl_label = 'Object operations'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'EI_Tools'

    def draw_header(self, context):
        layout = self.layout
        layout.label(text='', icon='MOD_SCREW')

    def draw(self, context):
        layout = self.layout
        row = layout.row()
        split = row.split(factor=0.35)
        left = split.column()
        # morphing
        row = layout.row()
        split = row.split(factor=1.2)
        left = split.column()
        row = layout.split()
        # row.prop(context.scene, 'morph_comp')
        left.operator('object.addmorphcomp', text='Copy as')
        row = layout.split()
        left.operator('object.addmorphcompnamed', text='Copy as name')
        left = left.split(factor=0.5)
        left.prop(context.scene, 'figcopy_name')
        #        row = layout.split()
        #        left = split.column()
        left.prop(context.scene, 'figcopy_parent')
        layout.operator('object.rename_drop_postfix')
        row = layout.split()
        split = split.column()
        split = row.split(factor=1.2)
        split.prop(context.scene, 'auto_replace')
        split = row.split(factor=5.0)
        split.prop(context.scene, 'morph1')
        split = row.split(factor=5.0)
        split.prop(context.scene, 'morph2')
        split = row.split(factor=5.0)
        split.prop(context.scene, 'morph3')
        row = layout.split()
        split = row.split(factor=5.0)
        split.prop(context.scene, 'morph4')
        split = row.split(factor=5.0)
        split.prop(context.scene, 'morph5')
        split = row.split(factor=5.0)
        split.prop(context.scene, 'morph6')
        split = row.split(factor=5.0)
        split.prop(context.scene, 'morph7')


class OPERATORMASS_PT_PANEL(bpy.types.Panel):
    bl_label = 'Mass operations'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'EI_Tools'

    def draw_header(self, context):
        layout = self.layout
        layout.label(text='', icon='MOD_SCREW')

    def draw(self, context):
        layout = self.layout

        row = layout.row()
        split = row.split(factor=1.35)
        # row.label(text='S')
        row.prop(context.scene, 's_s_x')
        row.prop(context.scene, 's_s_y')
        row.prop(context.scene, 's_s_z')

        row = layout.row()
        split = row.split(factor=1.35)
        # row.label(text='D')
        row.prop(context.scene, 's_d_x')
        row.prop(context.scene, 's_d_y')
        row.prop(context.scene, 's_d_z')

        row = layout.row()
        split = row.split(factor=1.35)
        # row.label(text='U')
        row.prop(context.scene, 's_u_x')
        row.prop(context.scene, 's_u_y')
        row.prop(context.scene, 's_u_z')

        layout = self.layout
        # layout.label(text='Animations')
        layout.prop(context.scene, 'scaled')

        row = layout.split()
        split = row.split(factor=1.2)
        split.prop(context.scene, 'auto_apply')
        split = row.split(factor=1.2)
        comp = split.column()
        comp.operator('object.copytoscaled', text='Copy all to scaled')
        row = self.layout
        row = layout.split()

        mesh_mask = context.scene.mesh_mask
        op_name = operators.CAutoFillMorphNew_OP_Operator.get_name(mesh_mask)
        row.operator('object.automorphnew', text=op_name).mesh_mask = mesh_mask
        row = layout.split()
        row.operator('object.fixpos', text='Fix positions')


class ANIMATION_PT_PANEL(bpy.types.Panel):
    bl_label = 'animations'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'EI_Tools'

    def draw_header(self, context):
        layout = self.layout
        layout.label(text='', icon='POSE_HLT')

    def draw(self, context):
        layout = self.layout
        # layout.label(text='Animations')
        scene = context.scene
        # model list
        row = layout.row()
        icon = 'TRIA_DOWN' if scene.show_animation_list else 'TRIA_RIGHT'
        row.prop(scene, 'show_animation_list', icon=icon, icon_only=True)
        row.label(text="Animations (.res)")
        if scene.show_animation_list:
            layout.template_list("LIST_RES_ANIMATIONS", "", scene, "animation_list", scene, "active_res_animation")
        ###
        layout.prop(scene, 'animation_name')
        layout.prop(scene, 'animsubfix')
        layout.prop(scene, 'is_animation_to_new_collection')
        target_collection = scene.animation_name if context.scene.is_animation_to_new_collection else "base"
        label = _(operators.CAnimationImport.bl_label) % target_collection
        layout.operator('object.animation_import', text=label)
        layout.prop(scene, 'is_use_mesh_frame_range')
        label = _(operators.CAnimationExport.bl_label) % target_collection
        layout.operator('object.animation_export', text=label)

        donor, acceptor = scene_utils.get_donor_acceptor(context)
        layout.label(text=_("SRC: %s") % (donor.name if donor else None))
        layout.label(text=_("DEST: %s") % (acceptor.name if acceptor else None))
        layout.operator('object.animation_shapekey')
        # layout.prop(context.scene, 'skeletal')
        layout.operator('object.animation_bake_transform')
        layout.operator('object.ue4_toolchain')
        # layout.separator()
        # layout.operator('object.debug_test')


def outliner_mt_collection(self: bpy.types.OUTLINER_MT_collection, context):
    layout = self.layout
    layout.separator()
    active_collection = context.view_layer.active_layer_collection
    active_collection_name = active_collection.name
    label = _(operators.CAnimationImport.bl_label) % active_collection_name
    layout.operator('object.animation_import', text=label)
    label = _(operators.CAnimationExport.bl_label) % active_collection_name
    layout.operator('object.animation_export', text=label)


def prepare_mesh_mask(context) -> str or None:
    selected_objects = context.view_layer.objects.selected
    base_coll = bpy.data.collections.get("base")

    export_names = []
    if not base_coll:
        return None
    for obj in selected_objects:
        if obj.name in base_coll.objects:
            export_names.append(obj.name)

    mesh_mask = None
    if export_names:
        mesh_mask = ','.join(export_names)
    return mesh_mask


def outliner_mt_object(self: bpy.types.OUTLINER_MT_object, context):
    layout = self.layout
    mesh_mask = prepare_mesh_mask(context)

    if not mesh_mask:
        return

    layout.separator()
    label = operators.CModelImport.get_name(mesh_mask)
    layout.operator('object.model_import', text=label).mesh_mask = mesh_mask
    label = operators.CModelExport.get_name(mesh_mask)
    layout.operator('object.model_export', text=label).mesh_mask = mesh_mask
    label = operators.CAutoFillMorphNew_OP_Operator.get_name(mesh_mask)
    layout.operator('object.automorphnew', text=label).mesh_mask = mesh_mask


def get_classes():
    return (
        EVIL_ISLANDS_PROPS,
        LIST_RES_MODELS,
        LIST_RES_ANIMATIONS,
        IMPORT_EXPORT_PT_PANEL,
        OPERATOR_PT_PANEL,
        OPERATORMASS_PT_PANEL,
        ANIMATION_PT_PANEL)
