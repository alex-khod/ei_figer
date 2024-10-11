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
import time
from bpy_extras.io_utils import ImportHelper
from . import scene_utils
from . figure import CFigure
from . bone import CBone
from . links import CLink
from . utils import *
from . scene_management import CModel
from . resfile import ResFile
from . scene_utils import *

def get_duration(fn):
    start_time = time.time()
    fn()
    duration = time.time() - start_time
    return duration

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

def clear_old_morphs(obj_list):
    scene = bpy.context.scene
    collections = bpy.data.collections
    if len(collections) == 1:
        return False
    for obj in obj_list:
        if obj.type != 'MESH':
            continue
        for coll_name in model().morph_collection[1:]:
            coll = collections.get(coll_name)
            if not coll:
                continue
            for obj in coll.objects:
                if obj.type != 'MESH':
                    continue
                coll = scene.collection.children[coll_name]
                del_name = obj.name
                #if (model().morph_comp[i] + obj.name) in coll.objects:
                bpy.data.objects.remove(bpy.data.objects[del_name])
    return True

class CAutoFillMorphNew_OP_Operator(bpy.types.Operator):
    bl_label = 'AutoMorphing'
    bl_idname = 'object.automorphnew'
    bl_description = 'Generates morph components based on existing -base- collection' \
                     'if you have animation going on, transformations will break it' \
                     'so make a copy beforehand' \

    def execute(self, context):

        collections = bpy.data.collections
        base_coll = collections.get("base")
        if not base_coll:
            self.report({'ERROR'}, 'No base collection')
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

        if clear_old_morphs(base_coll.objects):
            self.report({'INFO'}, 'Старые модели удалены/ old models deleted')

        for obj in base_coll.objects:
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

        vectors = [
            (scn.s_s_x, scn.s_s_y, scn.s_s_z),
            (scn.s_d_x, scn.s_d_y, scn.s_d_z),
            (scn.s_u_x, scn.s_u_y, scn.s_u_z),
            (scn.scaled, scn.scaled, scn.scaled),
            (scaled + scn.s_s_x - 1, scaled + scn.s_s_y - 1, scaled + scn.s_s_z - 1),
            (scaled + scn.s_d_x - 1, scaled + scn.s_d_y - 1, scaled + scn.s_d_z - 1),
            (scaled + scn.s_u_x - 1, scaled + scn.s_u_y - 1, scaled + scn.s_u_z - 1),
        ]

        for obj in bpy.context.selected_objects:
            obj.select_set(False)

        # привязываем родителей
        for s in range(1, 8):
            for child, parent in links.items():
                if parent is None:
                    continue
                bpy.data.objects[model().morph_comp[s] + child].parent = bpy.data.objects[
                    model().morph_comp[s] + parent]

        #Трогаем только scaled коллекции
        for s in range(1, 8):
            for child, parent in links.items():
                if parent is None:
                    bpy.data.objects[model().morph_comp[s] + child].scale = vectors[s - 1]

        for obj in bpy.context.selected_objects:
            obj.select_set(False)

        for i in range(0, 8):
            coll_name = model().morph_collection[i]
            coll = bpy.data.collections.get(coll_name)
            for obj in coll.objects:
                obj.select_set(True)
                bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
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

class CSelectResFileIndex(bpy.types.Operator):
    bl_label = 'Select Resfile'
    bl_idname = 'object.select_resfile'
    bl_description = 'Select this res file'

    res_file_index: bpy.props.IntProperty(
        default=0, options={'HIDDEN'},
    )

    def execute(self, context):
        context.scene.res_file = get_res_file_buffer(self.res_file_index)
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

    res_file_index: bpy.props.IntProperty(
        default=0, options={'HIDDEN'},
    )

    def execute(self, context):
        importlib.reload(scene_utils)
        scene_utils.set_res_file_buffer(self.res_file_index, self.filepath)
        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        wm.fileselect_add(self)
        return {'RUNNING_MODAL'}

class CClear_OP_operator(bpy.types.Operator):
    bl_label = 'Clear scene'
    bl_idname = 'object.clear_scene'
    bl_description = 'Should be pretty obvious'

    def execute(self, context: bpy.types.Context) -> set[str]:
        scene_clear()
        return {'FINISHED'}

class CImport_OP_operator(bpy.types.Operator):
    bl_label = 'EI model import Operator'
    bl_idname = 'object.model_import'
    bl_description = 'Import Model/Figure from selected resfile into base collection'

    def execute(self, context):
        self.report({'INFO'}, 'Executing import model')

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
            anm_list = anm_res_file.get_filename_list()
            if anm_name not in anm_list: #set of animations
                self.report({'ERROR'}, 'Can not find ' + anm_name +\
                    '\nAnimation list: ' + str(anm_list))
                return {'CANCELLED'}
        
        animations = read_animations(resFile, model_name, anm_name)
        links = collect_links() #Lost Soul - fix for rewrite animations after close file
        ei2abs_rotations(links, animations)
        bAutofix = bpy.context.scene.animsubfix
        if not bAutofix:     
            abs2Blender_rotations(links, animations)
        insert_animation(animations)
        self.report({'INFO'}, 'Done')
        return {'FINISHED'}

class CAnimation_OP_shapekey(bpy.types.Operator):
    bl_label = 'Shapekey animation Operator'
    bl_idname = 'object.animation_shapekey'
    bl_description = "Select two models, first Donor then Acceptor.\n" \
                     "Donor's vertex animation will be transferred as shapekeys to\n" \
                     "Acceptor."

    def execute(self, context):
        self.report({'INFO'}, 'Executing shapekey')

        importlib.reload(scene_utils)
        scene_utils.animation_to_shapekey(context)

        self.report({'INFO'}, 'Done')
        return {'FINISHED'}

class CAnimation_OP_BakeTransform(bpy.types.Operator):
    bl_label = 'Bake transform operator'
    bl_idname = 'object.animation_bake_transform'
    bl_description = 'For each object in selection, moves location / rotation / scale\n' \
                     'animation into shapekeys ignores objects with shapekeys (morph animation)'

    def execute(self, context):
        self.report({'INFO'}, 'Executing bake transform')
        selected = context.selected_objects

        if not selected:
            self.report({'ERROR'}, 'No object selected')
            return {"CANCELLED"}

        importlib.reload(scene_utils)
        duration = get_duration(lambda : scene_utils.bake_transform_animation(context))

        self.report({'INFO'}, f'Done in {duration:.2f} sec')
        return {'FINISHED'}


class CAnimation_OP_Export(bpy.types.Operator):
    bl_label = 'EI animation export Operator'
    bl_idname = 'object.animation_export'
    bl_description = 'Export Animations for model\n' \
                     'NOTE: Models with morph/shapekey animation need morph component scaling set to 1\n' \
                     'otherwise you\'ll get broken animation ingame'

    def execute(self, context):
        self.report({'INFO'}, 'Executing animation export')
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
        
        links = collect_links()
        animations = collect_animations()
        blender2abs_rotations(links, animations)
        abs2ei_rotations(links, animations)

        def write_animations(res_path, model_name, anm_name):
            #pack crrent animation first. byte array for each part (lh1, lh2, etc)
            anm_res = io.BytesIO()
            with ResFile(anm_res, 'w') as res:
                for part in animations:
                    with res.open(part.name, 'w') as file:
                        data = part.write_anm()
                        file.write(data)

            # read all animation data(uattack, udeath and etc) from figures
            export_model_name = model_name + '.anm'
            data = {}
            with (
                ResFile(res_path, "r") as figres,
                figres.open(export_model_name, "r") as anmfile,
                ResFile(anmfile, "r") as res
                ):
                for info in res.iter_files():
                    with res.open(info.name) as file:
                        data[info.name] = file.read()
            
            data[anm_name] = anm_res.getvalue() #modified animation set

            #write animations into res file
            with (
                ResFile(res_path, "a") as figres,
                figres.open(export_model_name, "w") as anmfile,
                ResFile(anmfile, "w") as res
                ):
                for name, anm_data in data.items():
                    with res.open(name, "w") as file:
                        file.write(anm_data)

            print(res_path + 'saved')

        write_animations(res_path, model_name, anm_name)

        self.report({'INFO'}, 'Done')
        return {'FINISHED'}

class CRenameDropPostfix_OP_operator(bpy.types.Operator):
    bl_label = 'EI model export Operator'
    bl_idname = 'object.rename_drop_postfix'
    bl_description = 'Rename selected objects as to drop .001 etc from the names'

    def execute(self, context):
        if not bpy.context.selected_objects:
            self.report({'ERROR'}, 'No object selected')
            return {"CANCELLED"}
        self.report({'INFO'}, 'Executing rename - drop postifx')
        for obj in bpy.context.selected_objects:
            name = obj.name.split('.')[0]
            obj.name = name
        self.report({'INFO'}, 'Done!')
        return {"FINISHED"}


        
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
        links = collect_links()
        active_model.pos_list.clear()
        collect_pos()
        collect_mesh()
        
        obj_count = CItemGroupContainer().get_item_group(model().name).morph_component_count
        if obj_count == 1: # save lnk,fig,bon into res (without model resfile)
            with ResFile(res_path, 'a') as res:
                with res.open(active_model.name + '.lnk', 'w') as file:
                    data = links.write_lnk()
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
                    data = links.write_lnk()
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