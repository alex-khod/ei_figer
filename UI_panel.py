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
        for index in range(0, 3):
            row = layout.row()
            elem = row.split(factor=0.8)
            elem.prop(context.scene, 'res_file_buffer%d' % index)
            elem.operator('object.choose_resfile', text='...').res_file_index = index
            elem.operator('object.select_resfile', text='Select').res_file_index = index
        layout.label(text=str(context.scene.res_file), icon='FILE_FOLDER')
        layout.prop(context.scene, 'figmodel_name')
        layout.operator('object.model_import', text='Import')
        row = layout.split()
        row.prop(context.scene, 'auto_fix')
        row.prop(context.scene, 'ether')
        row.operator('object.model_export', text='Export')
        row = layout.row()
        row.operator('object.clear_scene', text='Clear scene')


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
        #morphing
        row = layout.row()
        split = row.split(factor=1.2)
        left = split.column()
        row = layout.split()
        #row.prop(context.scene, 'morph_comp')
        left.operator('object.addmorphcomp', text='Copy as')
        row = layout.split()
        left.operator('object.addmorphcompnamed', text='Copy as name')
        left = left.split(factor=0.5)
        left.prop(context.scene, 'figcopy_name')
#        row = layout.split()
#        left = split.column()
        left.prop(context.scene, 'figcopy_parent')
        layout.operator('object.rename_drop_postfix', text='Drop .001 name part')
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
        #row.label(text='S')
        row.prop(context.scene, 's_s_x')
        row.prop(context.scene, 's_s_y')
        row.prop(context.scene, 's_s_z')

        row = layout.row()
        split = row.split(factor=1.35)
        #row.label(text='D')
        row.prop(context.scene, 's_d_x')
        row.prop(context.scene, 's_d_y')
        row.prop(context.scene, 's_d_z')

        row = layout.row()
        split = row.split(factor=1.35)
        #row.label(text='U')
        row.prop(context.scene, 's_u_x')
        row.prop(context.scene, 's_u_y')
        row.prop(context.scene, 's_u_z')

        layout = self.layout
        #layout.label(text='Animations')
        layout.prop(context.scene, 'scaled')
        
        row = layout.split()
        split = row.split(factor=1.2)
        split.prop(context.scene, 'auto_apply')
        split = row.split(factor=1.2)
        comp = split.column()
        comp.operator('object.copytoscaled', text='Copy all to scaled')
        row = self.layout
        row = layout.split()
        row.operator('object.automorphnew', text='Create all morps')
        row = layout.split()
        row.operator('object.fixpos', text='Fix positions')
       #automorph (in progress now)
        # row = layout.row()
        # row.operator('object.automorph', text="Auto Morph")


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
        #layout.label(text='Animations')
        layout.prop(context.scene, 'animation_name')
        layout.operator('object.animation_import', text='Import')
        layout.operator('object.animation_export', text='Export')
        layout.prop(context.scene, 'animsubfix')
        layout.operator('object.animation_shapekey', text='Shapekey')
        layout.prop(context.scene, 'skeletal')
        layout.operator('object.animation_bake_transform', text='Bake transform')

