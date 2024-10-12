# Copyright (c) 2022 konstvest
import importlib

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
import os
import io
from bpy_extras.io_utils import ImportHelper
from . import scene_utils
from . figure import CFigure
from . bone import CBone
from . links import CLink
from . utils import *
from . scene_management import CModel
from . resfile import ResFile
from . scene_utils import *
    

class CRefreshTestTable(bpy.types.Operator):
    bl_label = 'EI refresh test unit'
    bl_idname = 'object.refresh_test_unit'
    bl_description = 'delete current test unit and create new one'

    def execute(self, context):
        bpy.ops.object.select_all(action='DESELECT')
        tu_dict = dict()
        if bpy.types.Scene.model.morph_collection[8] in bpy.context.scene.collection.children.keys():
            bpy.data.collections.remove(bpy.data.collections[bpy.types.Scene.model.morph_collection[8]])
        #clean()
        bpy.types.Scene.model.mesh_list = []
        bpy.types.Scene.model.pos_lost = []
        bpy.types.Scene.model.fig_table.clear()
        bpy.types.Scene.model.bon_table.clear()
        to_object_mode()

        # find base objects
        for obj in bpy.data.objects:
            if obj.name in context.scene.collection.children[bpy.types.Scene.model.morph_collection[0]].objects and \
                not obj.hide_get() and obj.name[0:2] not in bpy.types.Scene.model.morph_comp:
                bpy.types.Scene.model.mesh_list.append(bpy.types.Scene.model.morph_comp[8] + obj.data.name)
                bpy.types.Scene.model.pos_lost.append(bpy.types.Scene.model.morph_comp[8] + obj.name)
                if obj.parent is None:
                    tu_dict[bpy.types.Scene.model.morph_comp[8] + obj.name] = None
                else:
                    tu_dict[bpy.types.Scene.model.morph_comp[8] + obj.name] = bpy.types.Scene.model.morph_comp[8] + obj.parent.name

        for test_mesh in bpy.types.Scene.model.mesh_list:
            cur_m = CFigure()
            cur_m.name = test_mesh
            cur_m.get_data_from_mesh(test_mesh[2:])
            bpy.types.Scene.model.fig_table[test_mesh] = cur_m
        for test_obj in bpy.types.Scene.model.pos_lost:
            cur_b = CBone()
            cur_b.name = test_obj
            cur_b.get_object_position(test_obj[2:])
            bpy.types.Scene.model.bon_table[test_obj] = cur_b

        for t_ind in bpy.types.Scene.model.mesh_list:
            bpy.types.Scene.model.fig_table[t_ind].create_mesh('non')
            if t_ind in bpy.data.objects:
                if bpy.types.Scene.model.morph_collection[8] not in bpy.context.scene.collection.children.keys():
                    colTest = bpy.data.collections.new(bpy.types.Scene.model.morph_collection[8])
                    bpy.context.scene.collection.children.link(colTest)
                bpy.context.scene.collection.children[bpy.types.Scene.model.morph_collection[8]].objects.link(bpy.data.objects[t_ind])
                bpy.context.scene.collection.children[bpy.types.Scene.model.morph_collection[0]].objects.unlink(bpy.data.objects[t_ind])
        linker = CLink()
        linker.create_hierarchy(tu_dict)
        for p_ind in bpy.types.Scene.model.pos_lost:
            bpy.types.Scene.model.bon_table[p_ind].set_pos('non')
        calculate_mesh(self, context)
        return {'FINISHED'}

class CAddMorphComp_OP_Operator(bpy.types.Operator):
    bl_label = 'EI Add Morphing Components'
    bl_idname = 'object.addmorphcomp'
    bl_description = 'Copy selected objects as morphing component'

    def execute(self, context):
        #prefix = bpy.context.scene.morph_comp
    
        def addMorphComp(prefix):
                
                  
            links = dict()
            childs = dict()
            clear_unlinked_data()
            scene = bpy.context.scene
            def get_true_name(name : str):
                return name[2:] if name[0:2] in model().morph_comp.values() else name

            col_num = list(model().morph_comp.keys())[list(model().morph_comp.values()).index(prefix)]
            if col_num > 0:
                previous_col_name = model().morph_collection[col_num-1]
                if previous_col_name not in scene.collection.children:
                    self.report({'ERROR'}, 'Previous collection \"'+ previous_col_name +'\" does not exist')
                    return {'CANCELLED'}
            

            bExist = False
            collections = bpy.context.scene.collection.children
            for obj in bpy.context.selected_objects:


                # save links
                #if obj in bpy.data.objects:
                 
                
                
                
                for objs in bpy.context.scene.collection.children['base'].objects:
                    if objs.parent is None:
                        links[prefix + get_true_name(objs.name)] = None
                    else:
                        links[prefix + get_true_name(objs.name)] = (prefix + get_true_name(objs.parent.name))
                
#                if obj.child is None:
#                    childs[prefix + true_name] = None
#                else:
#                    childs[prefix + true_name] = (prefix + get_true_name(obj.parent.name))

                #Сохраняем чайлдов у объекта
                #coll_name = model().morph_collection[col_num]
                #for obj in collections[col_num].objects:
                #    if obj.parent is (prefix + true_name):
                #        childs.add(obj.name)
                #        print(prefix + true_name + ' have child ' + obj.name)

                #Заменяем или ругаемся про существующий объект в целевой коллекции
                true_name = get_true_name(obj.name)
                if (prefix + true_name) in bpy.data.objects:
                    bReplace = bpy.context.scene.auto_replace
                    if not bReplace:
                        print(obj.name + ' already have this morph comp')
                        bExist = True
                        continue
                    else:
                       bpy.data.objects.remove(bpy.data.objects[prefix + true_name]) 
                   

                #coll = scene.collection.children[coll_name]
                #del_name = obj.name
                ##if (model().morph_comp[col_num] + obj.name) in coll.objects:
                #self.report({'INFO'}, 'Старые модели удалены/ old models deleted')
                #bpy.data.objects.remove(bpy.data.objects[del_name])



                

                # create copy of object
                new_obj = obj.copy()
                new_obj.name = prefix + true_name
                new_obj.data = obj.data.copy()
                new_obj.data.name = new_obj.name
                
                coll_name = model().morph_collection[list(model().morph_comp.keys())[list(model().morph_comp.values()).index(prefix)]]
                if coll_name not in scene.collection.children:
                    new_col = bpy.data.collections.new(coll_name)
                    scene.collection.children.link(new_col)
                coll = scene.collection.children[coll_name]
                coll.objects.link(new_obj)
                new_obj.select_set(False)
            
            if not links:
                self.report({'ERROR'}, 'Object(s) already have these morph components' if bExist else 'Empty objects to copy. Please select objects')
                return {'CANCELLED'}

            for child, parent in links.items():
                if parent is None:
                    continue
                bpy.data.objects[child].parent = bpy.data.objects[parent]
#            for child, parent in childs.items():
#                if child is None:
#                    continue
#                bpy.data.objects[parent].child = bpy.data.objects[child]

        if bpy.context.scene.morph1:
            addMorphComp('s~')
        if bpy.context.scene.morph2:
            addMorphComp('d~')
        if bpy.context.scene.morph3:
            addMorphComp('u~')
        if bpy.context.scene.morph4:
            addMorphComp('b~')
        if bpy.context.scene.morph5:
            addMorphComp('p~')
        if bpy.context.scene.morph6:
            addMorphComp('g~')
        if bpy.context.scene.morph7:
            addMorphComp('c~')


        
        self.report({'INFO'}, 'Done')
        return {'FINISHED'}



class CAddMorphCompNamed_OP_Operator(bpy.types.Operator):
    bl_label = 'EI Add named Morphing Components'
    bl_idname = 'object.addmorphcompnamed'
    bl_description = 'Copy selected objects as morphing component with slected name'

    def execute(self, context):
        #prefix = bpy.context.scene.morph_comp
    
        def addMorphComp(prefix):
                
                  
            links = dict()
            childs = dict()
            clear_unlinked_data()
            scene = bpy.context.scene
            
            
            newname = scene.figcopy_name
            newparent = scene.figcopy_parent
            
            
            def get_true_name(name : str):
                return name[2:] if name[0:2] in model().morph_comp.values() else name

            col_num = list(model().morph_comp.keys())[list(model().morph_comp.values()).index(prefix)]
            if col_num > 0:
                previous_col_name = model().morph_collection[col_num-1]
                if previous_col_name not in scene.collection.children:
                    self.report({'ERROR'}, 'Previous collection \"'+ previous_col_name +'\" does not exist')
                    return {'CANCELLED'}
            

            bExist = False
            collections = bpy.context.scene.collection.children
            for obj in bpy.context.selected_objects:


                # save links
                #if obj in bpy.data.objects:
                 
                
                
                
                for objs in collections['base'].objects:
                    if objs.parent is None:
                        links[prefix + get_true_name(objs.name)] = None
                    else:
                        links[prefix + get_true_name(objs.name)] = (prefix + get_true_name(objs.parent.name))
                
#                if obj.child is None:
#                    childs[prefix + true_name] = None
#                else:
#                    childs[prefix + true_name] = (prefix + get_true_name(obj.parent.name))

                #Сохраняем чайлдов у объекта
                #coll_name = model().morph_collection[col_num]
                #for obj in collections[col_num].objects:
                #    if obj.parent is (prefix + true_name):
                #        childs.add(obj.name)
                #        print(prefix + true_name + ' have child ' + obj.name)

                #Заменяем или ругаемся про существующий объект в целевой коллекции
                true_name = get_true_name(obj.name)
                true_namenew = get_true_name(newname)
                #if (prefix + true_name) in bpy.data.objects:
                if (prefix + true_namenew) in bpy.data.objects:
                    bReplace = bpy.context.scene.auto_replace
                    if not bReplace:
                        print(obj.name + ' already have this morph comp')
                        bExist = True
                        continue
                    else:
                       bpy.data.objects.remove(bpy.data.objects[prefix + true_namenew]) 
                   

                #coll = scene.collection.children[coll_name]
                #del_name = obj.name
                ##if (model().morph_comp[col_num] + obj.name) in coll.objects:
                #self.report({'INFO'}, 'Старые модели удалены/ old models deleted')
                #bpy.data.objects.remove(bpy.data.objects[del_name])



                
                
                # create copy of object
                new_obj = obj.copy()
                #new_obj.name = prefix + true_name
                new_obj.name = prefix + newname
                new_obj.data = obj.data.copy()
                new_obj.data.name = new_obj.name
                

                for parents in bpy.data.objects:
                    #self.report({'INFO'}, str(get_true_name(parents.name)) + newparent)
                    for obj in bpy.context.selected_objects:
                        #self.report({'INFO'}, prefix + (get_true_name(parents.name)) )
                        if (str(get_true_name(parents.name))) == newparent:
                            self.report({'INFO'}, newparent)
                            resu = bpy.data.objects[(prefix + get_true_name(parents.name))]
                            bpy.data.objects[new_obj.name].parent = resu


                coll_name = model().morph_collection[list(model().morph_comp.keys())[list(model().morph_comp.values()).index(prefix)]]
                if coll_name not in scene.collection.children:
                    new_col = bpy.data.collections.new(coll_name)
                    scene.collection.children.link(new_col)
                coll = scene.collection.children[coll_name]
                coll.objects.link(new_obj)
                new_obj.select_set(False)
            
            if not links:
                self.report({'ERROR'}, 'Object(s) already have these morph components' if bExist else 'Empty objects to copy. Please select objects')
                return {'CANCELLED'}

#            for child, parent in childs.items():
#                if child is None:
#                    continue
#                bpy.data.objects[parent].child = bpy.data.objects[child]

        if bpy.context.scene.morph1:
            addMorphComp('s~')
        if bpy.context.scene.morph2:
            addMorphComp('d~')
        if bpy.context.scene.morph3:
            addMorphComp('u~')
        if bpy.context.scene.morph4:
            addMorphComp('b~')
        if bpy.context.scene.morph5:
            addMorphComp('p~')
        if bpy.context.scene.morph6:
            addMorphComp('g~')
        if bpy.context.scene.morph7:
            addMorphComp('c~')

        
        self.report({'INFO'}, 'Done')
        return {'FINISHED'}


class CAddAllMorphComp_OP_Operator(bpy.types.Operator):
    bl_label = 'EI Add Morphing Components'
    bl_idname = 'object.addallmorphcomp'
    bl_description = 'Copy selected objects as morphing component'

    def execute(self, context):
        prefix = bpy.context.scene.morph_comp
        links = dict()
        clear_unlinked_data()
        scene = bpy.context.scene
        def get_true_name(name : str):
            return name[2:] if name[0:2] in model().morph_comp.values() else name

        col_num = list(model().morph_comp.keys())[list(model().morph_comp.values()).index(prefix)]
        if col_num > 0:
            previous_col_name = model().morph_collection[col_num-1]
            if previous_col_name not in scene.collection.children:
                self.report({'ERROR'}, 'Previous collection \"'+ previous_col_name +'\" does not exist')
                return {'CANCELLED'}
        
        bExist = False
        for obj in bpy.context.selected_objects:
            true_name = get_true_name(obj.name)
            if (prefix + true_name) in bpy.data.objects:
                print(obj.name + ' already have this morph comp')
                bExist = True
                continue
            
            # save links
            if obj.parent is None:
                links[prefix + true_name] = None
            else:
                links[prefix + true_name] = (prefix + get_true_name(obj.parent.name))

            # create copy of object
            new_obj = obj.copy()
            new_obj.name = prefix + true_name
            new_obj.data = obj.data.copy()
            new_obj.data.name = new_obj.name
            
            coll_name = model().morph_collection[list(model().morph_comp.keys())[list(model().morph_comp.values()).index(prefix)]]
            if coll_name not in scene.collection.children:
                new_col = bpy.data.collections.new(coll_name)
                scene.collection.children.link(new_col)
            coll = scene.collection.children[coll_name]
            coll.objects.link(new_obj)
            new_obj.select_set(False)
        
        if not links:
            self.report({'ERROR'}, 'Object(s) already have these morph components' if bExist else 'Empty objects to copy. Please select objects')
            return {'CANCELLED'}

        for child, parent in links.items():
            if parent is None:
                continue
            bpy.data.objects[child].parent = bpy.data.objects[parent]
        
        self.report({'INFO'}, 'Done')
        return {'FINISHED'}




class CAutoFillMorph_OP_Operator(bpy.types.Operator):
    bl_label = 'AutoMorphing'
    bl_idname = 'object.automorph'
    bl_description = 'Generates morph components based on existing once'

    def execute(self, context):

        collections = bpy.context.scene.collection.children
        if len(collections) < 0:
            self.report({'ERROR'}, 'Scene empty')
            return {'CANCELLED'}
        if collections[0].name != model().morph_collection[0]:
            self.report({'ERROR'}, 'Base collection must be named as \"base\"')
            return {'CANCELLED'}

        model().name = bpy.context.scene.figmodel_name
        if not model().name:
            self.report({'ERROR'}, 'Model name is empty')
            return {'CANCELLED'}
        
        item = CItemGroupContainer().get_item_group(model().name)
        obj_count = item.morph_component_count
        if obj_count == 1:
            self.report({'INFO'}, 'This object type has only 1 collection \"base\"')
            return {'CANCELLED'}
        
        clear_unlinked_data()
        scene = bpy.context.scene

        links = dict()
        for obj in collections[0].objects:
            if obj.type != 'MESH':
                continue
            links[obj.name] = None if obj.parent is None else obj.parent.name
            for i in range(1, 8):
                coll_name = model().morph_collection[i]
                if coll_name not in scene.collection.children:
                    new_col = bpy.data.collections.new(coll_name)
                    scene.collection.children.link(new_col)
                coll = scene.collection.children[coll_name]
                morph_name = model().morph_comp[i]
                if morph_name in coll.objects:
                    continue

                #detect suitable obj
                new_obj: bpy.types.Object = obj.copy()
                new_obj.name = model().morph_comp[i] + obj.name
                new_obj.data = obj.data.copy()
                new_obj.data.name = new_obj.name
                coll.objects.link(new_obj)
                new_obj.select_set(False)
            
            for i in range(1, 8):
                for child, parent in links.items():
                    if parent is None:
                        continue
                    bpy.data.objects[model().morph_comp[i] + child].parent =\
                        bpy.data.objects[model().morph_comp[i] + parent]


        return {'FINISHED'}

class CAutoFillMorphNew_OP_Operator(bpy.types.Operator):
    bl_label = 'AutoMorphing'
    bl_idname = 'object.automorphnew'
    bl_description = 'Generates morph components based on existing -base- collection ? ' \
                     'if you have animation going on, set frame beyond animation range'

    def execute(self, context):
        collections = bpy.context.scene.collection.children
        if len(collections) < 0:
            self.report({'ERROR'}, 'Scene empty')
            return {'CANCELLED'}
        if collections[0].name != model().morph_collection[0]:
            self.report({'ERROR'}, 'Base collection must be named as \"base\"')
            return {'CANCELLED'}

        model().name = bpy.context.scene.figmodel_name
        if not model().name:
            self.report({'ERROR'}, 'Model name is empty')
            return {'CANCELLED'}
        
        item = CItemGroupContainer().get_item_group(model().name)
        obj_count = item.morph_component_count
        if obj_count == 1:
            self.report({'INFO'}, 'This object type has only 1 collection \"base\"')
            return {'CANCELLED'}
        
        clear_unlinked_data()
        scene = bpy.context.scene
        links = dict()
        # Триангулируем и применяем модификаторы на базовой модели
        bAutofix = bpy.context.scene.auto_apply
        if bAutofix:
            auto_fix_scene()

        scn = scene
        scaled = scn.scaled
        # удаляем старые модели
        for obj in collections[0].objects:
            if obj.type != 'MESH':
                continue
            for i in range(1, 8):
                if len(collections) == 1:
                    continue
                coll_name = model().morph_collection[i]
                for obj in collections[i].objects:
                    if obj.type != 'MESH':
                        continue
                    coll = scene.collection.children[coll_name]
                    del_name = obj.name
                    #if (model().morph_comp[i] + obj.name) in coll.objects:
                    self.report({'INFO'}, 'Старые модели удалены/ old models deleted')
                    bpy.data.objects.remove(bpy.data.objects[del_name])


        for obj in collections[0].objects:
            if obj.type != 'MESH':
                continue
            links[obj.name] = None if obj.parent is None else obj.parent.name
        # добавляем коллекции
            for i in range(1, 8):
                coll_name = model().morph_collection[i]
                if coll_name not in scene.collection.children:
                    new_col = bpy.data.collections.new(coll_name)
                    scene.collection.children.link(new_col)

                coll = scene.collection.children[coll_name]
                morph_name = model().morph_comp[i]
                if morph_name in coll.objects:
                    continue
        # копируем меши
                #detect suitable obj

                new_obj = obj.copy()
                new_obj.name = model().morph_comp[i] + obj.name
                new_obj.data = obj.data.copy()
                # all my homies hate animation
                new_obj.animation_data_clear()
                new_obj.shape_key_clear()
                new_obj.data.name = new_obj.name
                coll.objects.link(new_obj)
                new_obj.select_set(False)
        # привязываем родителей
        for c in range(1, 8):
            for obj in collections[c].objects:
                for child, parent in links.items():
                    if parent is None:
                        continue
                    bpy.data.objects[model().morph_comp[c] + child].parent = bpy.data.objects[model().morph_comp[c] + parent]
        for obj in bpy.context.selected_objects:
            obj.select_set(False)
        #Трогаем только scaled коллекции
        for s in range(1, 8):
            for obj in collections[s].objects:
                for child, parent in links.items():
                    if parent is None:
                        if s == 1:
                            bpy.data.objects[model().morph_comp[s] + child].scale = (scn.s_s_x, scn.s_s_y, scn.s_s_z)
                        if s == 2:
                            bpy.data.objects[model().morph_comp[s] + child].scale = (scn.s_d_x, scn.s_d_y, scn.s_d_z)
                        if s == 3:
                            bpy.data.objects[model().morph_comp[s] + child].scale = (scn.s_u_x, scn.s_u_y, scn.s_u_z)
                        if s == 4:
                            bpy.data.objects[model().morph_comp[s] + child].scale = (scn.scaled, scn.scaled, scn.scaled)
                        if s == 5:
                            bpy.data.objects[model().morph_comp[s] + child].scale = (scaled+scn.s_s_x-1, scaled+scn.s_s_y-1, scaled+scn.s_s_z-1)
                        if s == 6:
                            bpy.data.objects[model().morph_comp[s] + child].scale = (scaled+scn.s_d_x-1, scaled+scn.s_d_y-1, scaled+scn.s_d_z-1)
                        if s == 7:
                            bpy.data.objects[model().morph_comp[s] + child].scale = (scaled+scn.s_u_x-1, scaled+scn.s_u_y-1, scaled+scn.s_u_z-1)
                        
                        
        for obj in bpy.context.selected_objects:
            obj.select_set(False)
        for obj in bpy.data.objects:
        # Применяем все трансформации
            obj.select_set(True)
            bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
        #for obj in bpy.context.selected_objects:
            obj.select_set(False)

        return {'FINISHED'}


class CFixPos_OP_Operator(bpy.types.Operator):
    bl_label = 'FixPos'
    bl_idname = 'object.fixpos'
    bl_description = 'Generates morph components based on existing -base- collection'

    def execute(self, context):

        selected_obs = context.selected_objects
        ob_a = context.object
        mwi = ob_a.matrix_world.inverted()
        for ob_b in selected_obs:
            #local_pos = mwi * ob_b.matrix_world.translation
            local_pos = mwi @ ob_b.matrix_world.Identity(4).translation
            #local_pos = mwi @ ob_b.location
            #local_pos = mwi @ ob_b.matrix_world.Identity(4).location
            print(ob_b.name, local_pos)
                
        self.report({'INFO'}, 'Done')
        return {'FINISHED'}


class CAutoFillMorphScaledOnly_OP_Operator(bpy.types.Operator):
    bl_label = 'CopyToScaled'
    bl_idname = 'object.copytoscaled'
    bl_description = 'Generates SCALED morph components based on existing 4 base/str/dex/unic'

    def execute(self, context):
        collections = bpy.context.scene.collection.children
        if len(collections) < 0:
            self.report({'ERROR'}, 'Scene empty')
            return {'CANCELLED'}
        if collections[0].name != model().morph_collection[0]:
            self.report({'ERROR'}, 'Base collection must be named as \"base\"')
            return {'CANCELLED'}

        model().name = bpy.context.scene.figmodel_name
        if not model().name:
            self.report({'ERROR'}, 'Model name is empty')
            return {'CANCELLED'}
        
        item = CItemGroupContainer().get_item_group(model().name)
        obj_count = item.morph_component_count
        if obj_count == 1:
            self.report({'INFO'}, 'This object type has only 1 collection \"base\"')
            return {'CANCELLED'}
        def get_true_name(name : str):
            return name[2:] if name[0:2] in model().morph_comp.values() else name
        
        clear_unlinked_data()
        scene = bpy.context.scene
        links = dict()
        # Триангулируем и применяем модификаторы на базовой модели
        bAutofix = bpy.context.scene.auto_apply
        if bAutofix:
            auto_fix_scene()

        scn = scene
        scaled = scn.scaled
        # удаляем старые модели
        for obj in collections[0].objects:
            if obj.type != 'MESH':
                continue
            for i in range(4, 8):
                if len(collections) == 1:
                    continue
                coll_name = model().morph_collection[i]
                for obj in collections[i].objects:
                    if obj.type != 'MESH':
                        continue
                    coll = scene.collection.children[coll_name]
                    del_name = obj.name
                    #if (model().morph_comp[i] + obj.name) in coll.objects:
                    self.report({'INFO'}, 'Старые модели удалены/ old models deleted')
                    bpy.data.objects.remove(bpy.data.objects[del_name])

        for mc in range(0, 4):
            for obj in collections[mc].objects:
                if obj.type != 'MESH':
                    continue
                links[obj.name] = None if obj.parent is None else obj.parent.name
            # добавляем коллекции
                #for i in range(4, 7):
                coll_name = model().morph_collection[mc+4]
                if coll_name not in scene.collection.children:
                    new_col = bpy.data.collections.new(coll_name)
                    scene.collection.children.link(new_col)

                coll = scene.collection.children[coll_name]
                morph_name = model().morph_comp[mc+4]
                #if morph_name in coll.objects:
                #    continue
            # копируем меши
                    #detect suitable obj
                new_obj = obj.copy()
                new_obj.name = model().morph_comp[mc+4] + get_true_name(obj.name)
                new_obj.data = obj.data.copy()
                new_obj.data.name = new_obj.name
                coll.objects.link(new_obj)
                new_obj.select_set(False)
            # привязываем родителей
            #for c in range(4, 7):
            for obj in collections[mc+4].objects:
                for child, parent in links.items():
                    if parent is None:
                        continue
                    bpy.data.objects[model().morph_comp[mc+4] + get_true_name(child)].parent = bpy.data.objects[model().morph_comp[mc+4] + get_true_name(parent)]
            for obj in bpy.context.selected_objects:
                obj.select_set(False)
            #Трогаем только scaled коллекции
            #for s in range(4, 7):
            for obj in collections[mc+4].objects:
                for child, parent in links.items():
                    if parent is None:
                        #continue
                        bpy.data.objects[model().morph_comp[mc+4] + get_true_name(child)].scale = (scaled, scaled, scaled)
                            
                            
            for obj in bpy.context.selected_objects:
                obj.select_set(False)
            for obj in bpy.data.objects:
            # Применяем все трансформации
                obj.select_set(True)
                bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
            #for obj in bpy.context.selected_objects:
                obj.select_set(False)

        return {'FINISHED'}

class CChooseResFile(bpy.types.Operator, ImportHelper):
    '''
    Operator to choose *.res file
    '''
    bl_label = 'Choose Resfile'
    bl_idname = 'object.choose_resfile'
    bl_description = 'Select *.res file containing models, figures, animations. Usually Figures.res'
    
    filename_ext = ".res"

    filter_glob: bpy.props.StringProperty(
        default="*.res",
        options={'HIDDEN'},
        maxlen=255,  # Max internal buffer length, longer would be clamped.
    )

    def execute(self, context):
        bpy.context.scene.res_file = self.filepath
        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        wm.fileselect_add(self)
        return {'RUNNING_MODAL'}

class CImport_OP_operator(bpy.types.Operator):
    bl_label = 'EI model import Operator'
    bl_idname = 'object.model_import'
    bl_description = 'Import Model/Figure from Evil Islands file'

    def execute(self, context):
        self.report({'INFO'}, 'Executing import model')
        scene_clear()
        res_path = bpy.context.scene.res_file
        if not res_path or not os.path.exists(res_path):
            self.report({'ERROR'}, 'Res file not found at:' + res_path)
            return {'CANCELLED'}
        
        model_name : bpy.props.StringProperty = bpy.context.scene.figmodel_name
        if not model_name:
            self.report({'ERROR'}, 'Model/Figure name is empty')
            return {'CANCELLED'}

        active_model : CModel = bpy.types.Scene.model
        resFile = ResFile(res_path)
        if (model_name + '.mod') in resFile.get_filename_list():
            active_model.reset('fig')
            active_model.name = model_name
            read_model(resFile, model_name)
#            if read_figSignature(resFile, model_name) == 8:          ##LostSoul
            bEtherlord = bpy.context.scene.ether
            if not bEtherlord:
                read_bones(resFile, model_name)
#                break
            for fig in active_model.mesh_list:
                create_mesh_2(fig)
            create_links_2(active_model.links)
            for bone in active_model.pos_list:
                set_pos_2(bone)
        elif (model_name + '.lnk') in resFile.get_filename_list():
            # read lnk, fig, bone in source res file, not from .mod
            active_model.reset('fig')
            active_model.name = model_name
            err = read_links(resFile, model_name + '.lnk')
            renamed_dict = dict()
            for part, parent in active_model.links.links.items():
                if parent is None:
                    renamed_dict[active_model.name + part] = None
                else:
                    renamed_dict[active_model.name + part] = active_model.name + parent
            active_model.links.links = renamed_dict
            if err == 0:
                #read parts
                for part in active_model.links.links.keys():
                    if (part + '.fig') in resFile.get_filename_list():
                        read_figure(resFile, part + '.fig')
                        nnn = (active_model.mesh_list[-1].name.split(model_name)[1]).rsplit('.')[0] #TODO: nnn
                        active_model.mesh_list[-1].name = nnn
                    else:
                        print(part + '.fig not found')
                    
                    if (part + '.bon') in resFile.get_filename_list():
                        read_bone(resFile, part + '.bon')
                    else:
                        print(part + '.bon not found')
            #RuntimeError('Stopping the script here')
            for fig in active_model.mesh_list:
                create_mesh_2(fig)

            create_links_2(active_model.links)
            for bone in active_model.pos_list:
                set_pos_2(bone)
        else:
            item_list = list()
            for name in resFile.get_filename_list():
                if name.lower().endswith('.mod') or name.lower().endswith('.lnk'):
                    item_list.append(name.rsplit('.')[0])

            self.report({'ERROR'}, 'Can not find ' + model_name +\
                '\nItems list: ' + str(item_list))
            return {'CANCELLED'}
        
        self.report({'INFO'}, 'Done')
        return {'FINISHED'}

class CAnimation_OP_import(bpy.types.Operator):
    bl_label = 'EI animation import Operator'
    bl_idname = 'object.animation_import'
    bl_description = 'Import Animations for model'

    def execute(self, context):
        self.report({'INFO'}, 'Executing annimation import')
        res_path = bpy.context.scene.res_file
        if not res_path or not os.path.exists(res_path):
            self.report({'ERROR'}, 'Res file not found at:' + res_path)
            return {'CANCELLED'}
        
        anm_name = bpy.context.scene.animation_name
        model_name = bpy.context.scene.figmodel_name
        resFile = ResFile(res_path)
        
        if not model_name:
            self.report({'ERROR'}, 'Model/Figure name is empty')
            return {'CANCELLED'}

        if not anm_name:
            self.report({'ERROR'}, 'Animation name is empty')
            return {'CANCELLED'}

        #choosing model to load
        if model_name+'.anm' not in resFile.get_filename_list():
            self.report({'ERROR'}, 'Animations set for ' + model_name + 'not found')
            return {'CANCELLED'}

        with resFile.open(model_name + '.anm') as animation_container:
            anm_res_file = ResFile(animation_container)
            anm_list =  anm_res_file.get_filename_list()
            if anm_name not in anm_list: #set of animations
                self.report({'ERROR'}, 'Can not find ' + anm_name +\
                    '\nAnimation list: ' + str(anm_list))
                return {'CANCELLED'}
        
        active_model : CModel = bpy.types.Scene.model
        active_model.reset('anm')

        read_animations(resFile, model_name, anm_name)
        collect_links() #Lost Soul - fix for rewrite animations after close file
        ei2abs_rorations()
        bAutofix = bpy.context.scene.animsubfix
        if not bAutofix:     
            abs2Blender_rotations()
        insert_animation(active_model.anm_list)
        self.report({'INFO'}, 'Done')
        return {'FINISHED'}

class CAnimation_OP_shapekey(bpy.types.Operator):
    bl_label = 'Shapekey animation Operator'
    bl_idname = 'object.animation_shapekey'
    bl_description = "Select two models, first Donor then Acceptor. " \
                     "Donor's vertex animation will be transferred as shapekeys to " \
                     "Acceptor."

    def execute(self, context):
        self.report({'INFO'}, 'Executing shapekey')

        importlib.reload(scene_utils)
        # active_model: CModel = bpy.types.Scene.model
        scene_utils.animation_to_shapekey(context)

        self.report({'INFO'}, 'Done')
        return {'FINISHED'}

class CAnimation_OP_BakeTransform(bpy.types.Operator):
    bl_label = 'Bake transform operator'
    bl_idname = 'object.animation_bake_transform'
    bl_description = 'For each object in selection, moves location' \
                     ' / rotation / scale animation into shapekeys'

    def execute(self, context):
        self.report({'INFO'}, 'Executing bake transform')

        importlib.reload(scene_utils)
        scene_utils.animation_bake_transform(context)

        self.report({'INFO'}, 'Done')
        return {'FINISHED'}


class CAnimation_OP_Export(bpy.types.Operator):
    bl_label = 'EI animation export Operator'
    bl_idname = 'object.animation_export'
    bl_description = 'Export Animations for model'

    def execute(self, context):
        self.report({'INFO'}, 'Executing annimation export')
        res_path = bpy.context.scene.res_file
        if not res_path or not os.path.exists(res_path):
            self.report({'ERROR'}, 'Res file not found at:' + res_path)
            return {'CANCELLED'}  

        anm_name = bpy.context.scene.animation_name
        model_name = bpy.context.scene.figmodel_name
        #resFile = ResFile(res_path)
        
        if not model_name:
            self.report({'ERROR'}, 'Model/Figure name is empty')
            return {'CANCELLED'}

        if not anm_name:
            self.report({'ERROR'}, 'Animation name is empty')
            return {'CANCELLED'}
        
        active_model : CModel = bpy.types.Scene.model
        active_model.reset('anm')
        collect_links()
        collect_animations()
        blender2abs_rotations()
        abs2ei_rotations()

        def write_animations():
            nonlocal res_path
            nonlocal anm_name
            nonlocal model_name

            #pack crrent animation first. byte array for each part (lh1, lh2, etc)
            anm_res = io.BytesIO()
            with ResFile(anm_res, 'w') as res:
                for part in active_model.anm_list:
                    with res.open(part.name, 'w') as file:
                        data = part.write_anm()
                        file.write(data)

            # read all animation data(uattack, udeath and etc) from figures
            anm_name = anm_name
            model_name = model_name + '.anm'
            data = {}
            with (
                ResFile(res_path, "r") as figres,
                figres.open(model_name, "r") as anmfile,
                ResFile(anmfile, "r") as res
                ):
                for info in res.iter_files():
                    with res.open(info.name) as file:
                        data[info.name] = file.read()
            
            data[anm_name] = anm_res.getvalue() #modified animation set

            #write animations into res file
            with (
                ResFile(res_path, "a") as figres,
                figres.open(model_name, "w") as anmfile,
                ResFile(anmfile, "w") as res
                ):
                for name, anm_data in data.items():
                    with res.open(name, "w") as file:
                        file.write(anm_data)

            print(res_path + 'saved')


        write_animations()

        self.report({'INFO'}, 'Done')
        return {'FINISHED'}
        
class CExport_OP_operator(bpy.types.Operator):
    bl_label = 'EI model export Operator'
    bl_idname = 'object.model_export'
    bl_description = 'Export Evil Islands Model/Figure file'

    def execute(self, context):
        self.report({'INFO'}, 'Executing export')
        res_path = bpy.context.scene.res_file
        if not res_path:
            self.report({'ERROR'}, 'res file empty')
            return {'CANCELLED'}

        model_name : bpy.props.StringProperty = bpy.context.scene.figmodel_name
        if not model_name:
            self.report({'ERROR'}, 'Model/Figure name is empty')
            return {'CANCELLED'}

        active_model : CModel = bpy.types.Scene.model
        active_model.name = model_name
        active_model.reset()

        bAutofix = bpy.context.scene.auto_fix
        if bAutofix:
            auto_fix_scene()


        if not is_model_correct():
            self.report({'ERROR'}, 'Model/Figure cannot pass check. \nSee System Console (Window->Toggle System Console)')
            return {'CANCELLED'}
        collect_links()
        active_model.pos_list.clear()
        collect_pos()
        collect_mesh()
        
        obj_count = CItemGroupContainer().get_item_group(model().name).morph_component_count
        if obj_count == 1: # save lnk,fig,bon into res (without model resfile)
            with ResFile(res_path, 'a') as res:
                with res.open(active_model.name + '.lnk', 'w') as file:
                    data = active_model.links.write_lnk()
                    file.write(data)
            #write figs
            with ResFile(res_path, 'a') as res:
                for mesh in active_model.mesh_list:
                    mesh.name = model_name + mesh.name + '.fig'
                    with res.open(mesh.name, 'w') as file:
                        data = mesh.write_fig()
                        file.write(data)
            #write bones
            with ResFile(res_path, 'a') as res:
                for bone in active_model.pos_list:
                    bone.name = model_name + bone.name + '.bon'
                    with res.open(bone.name, 'w') as file:
                        data = bone.write_bon()
                        file.write(data)
        else:
            # prepare links + figures (.mod file)
            model_res = io.BytesIO()
            with ResFile(model_res, 'w') as res:
                # write lnk
                with res.open(active_model.name, 'w') as file:
                    data = active_model.links.write_lnk()
                    file.write(data)
                #write meshes
                for part in active_model.mesh_list:
                    with res.open(part.name, 'w') as file:
                        data = part.write_fig()
                        file.write(data)
            
            #prepare bons file (.bon file)
            bone_res = io.BytesIO()
            with ResFile(bone_res, 'w') as res:
                for part in active_model.pos_list:
                    with res.open(part.name, 'w') as file:
                        data = part.write_bon()
                        file.write(data)

            with ResFile(res_path, 'a') as res:
                with res.open(active_model.name + '.mod', 'w') as file:
                    file.write(model_res.getvalue())
                with res.open(active_model.name + '.bon', 'w') as file:
                    file.write(bone_res.getvalue())
                
            print('resfile ' + res_path + ' saved')
        self.report({'INFO'}, 'Done')
        return {'FINISHED'}