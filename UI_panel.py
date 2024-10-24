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

from . import scene_utils
from . import operators

from bpy.app import translations
_ = translations.pgettext


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
        layout.label(text=str(context.scene.res_file), icon='FILE_FOLDER')
        for index in range(0, 3):
            row = layout.row()
            elem = row.split(factor=0.8)
            elem.prop(context.scene, 'res_file_buffer%d' % index)
            elem.operator('object.choose_resfile', text='...').res_file_index = index
            elem.operator('object.select_resfile', text="✓").res_file_index = index
        layout.prop(context.scene, 'figmodel_name')
        layout.prop(context.scene, 'mesh_mask')
        mesh_mask = context.scene.mesh_mask
        op_name = operators.CImport_OP_operator.get_name(mesh_mask)
        layout.operator('object.model_import', text=op_name).mesh_mask = mesh_mask
        row = layout.split()
        row.prop(context.scene, 'auto_fix')
        row.prop(context.scene, 'ether')
        row.prop(context.scene, 'is_export_unique', text="compact")
        layout.prop(context.scene, 'is_ignore_without_morphs')
        op_name = operators.CExport_OP_operator.get_name(mesh_mask)
        layout.operator('object.model_export', text=op_name).mesh_mask = mesh_mask
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
        layout.prop(context.scene, 'animation_name')

        layout.prop(context.scene, 'animsubfix')
        layout.prop(context.scene, 'is_animation_to_new_collection')
        use_collection = context.scene.animation_name if context.scene.is_animation_to_new_collection else "base"
        label = _(operators.CAnimation_OP_import.bl_label) % use_collection
        layout.operator('object.animation_import', text=label).target_collection = use_collection
        layout.prop(context.scene, 'is_use_mesh_frame_range')
        label = _(operators.CAnimation_OP_Export.bl_label) % use_collection
        layout.operator('object.animation_export', text=label).target_collection = use_collection

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
    label = _(operators.CAnimation_OP_import.bl_label) % active_collection_name
    layout.operator('object.animation_import', text=label).target_collection = active_collection_name
    label = _(operators.CAnimation_OP_Export.bl_label) % active_collection_name
    layout.operator('object.animation_export', text=label).target_collection = active_collection_name


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
    label = operators.CImport_OP_operator.get_name(mesh_mask)
    layout.operator('object.model_import', text=label).mesh_mask = mesh_mask
    label = operators.CExport_OP_operator.get_name(mesh_mask)
    layout.operator('object.model_export', text=label).mesh_mask = mesh_mask
    label = operators.CAutoFillMorphNew_OP_Operator.get_name(mesh_mask)
    layout.operator('object.automorphnew', text=label).mesh_mask = mesh_mask
