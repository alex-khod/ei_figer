# Copyright (c) 2022 konstvest
import importlib
import os
import time

#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
import bpy
from bpy import props
from bpy_extras.io_utils import ImportHelper

from . import animation
from . import bone
from . import figure
from . import resfile
from . import scene_management
from . import scene_utils
from . import utils as fig_utils
from .bone import CBone
from .figure import CFigure
from .links import CLink
from .scene_utils import MODEL, clear_unlinked_data

# This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.

ResFile = resfile.ResFile

from bpy.app import translations

_ = translations.pgettext


def call_with_time(fn):
    start_time = time.time()
    res = fn()
    duration = time.time() - start_time
    return res, duration


def get_name(cls, mesh_mask):
    if mesh_mask:
        text = str(len(mesh_mask.split(',')))
    else:
        base_coll = scene_utils.get_collection("base")
        text = str(len(base_coll.objects)) if base_coll else "all"
    return _(cls.bl_label) % text


def reload_modules():
    importlib.reload(bone)
    importlib.reload(scene_utils)
    importlib.reload(figure)
    importlib.reload(fig_utils)
    importlib.reload(scene_management)
    importlib.reload(animation)
    # doesn't reload resfile?
    importlib.reload(resfile)


class CRefreshTestTable(bpy.types.Operator):
    bl_label = 'EI refresh test unit'
    bl_idname = 'object.refresh_test_unit'
    bl_description = 'delete current test unit and create new one'

    def execute(self, context):
        bpy.ops.object.select_all(action='DESELECT')
        tu_dict = dict()
        if bpy.types.Scene.model.morph_collection[8] in bpy.context.scene.collection.children.keys():
            bpy.data.collections.remove(bpy.data.collections[bpy.types.Scene.model.morph_collection[8]])
        # clean()
        bpy.types.Scene.model.mesh_list = []
        bpy.types.Scene.model.pos_lost = []
        bpy.types.Scene.model.fig_table.clear()
        bpy.types.Scene.model.bon_table.clear()
        scene_utils.to_object_mode()

        # find base objects
        for obj in bpy.data.objects:
            if obj.name in context.scene.collection.children[
                bpy.types.Scene.model.morph_collection[0]].objects and not obj.hide_get() and obj.name[
                                                                                              0:2] not in bpy.types.Scene.model.morph_comp:
                bpy.types.Scene.model.mesh_list.append(bpy.types.Scene.model.morph_comp[8] + obj.data.name)
                bpy.types.Scene.model.pos_lost.append(bpy.types.Scene.model.morph_comp[8] + obj.name)
                if obj.parent is None:
                    tu_dict[bpy.types.Scene.model.morph_comp[8] + obj.name] = None
                else:
                    tu_dict[bpy.types.Scene.model.morph_comp[8] + obj.name] = bpy.types.Scene.model.morph_comp[
                                                                                  8] + obj.parent.name

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
                bpy.context.scene.collection.children[bpy.types.Scene.model.morph_collection[8]].objects.link(
                    bpy.data.objects[t_ind])
                bpy.context.scene.collection.children[bpy.types.Scene.model.morph_collection[0]].objects.unlink(
                    bpy.data.objects[t_ind])
        linker = CLink()
        linker.create_hierarchy(tu_dict)
        for p_ind in bpy.types.Scene.model.pos_lost:
            bpy.types.Scene.model.bon_table[p_ind].set_pos('non')
        scene_utils.calculate_mesh(self, context)
        return {'FINISHED'}


class CAddMorphComp_OP_Operator(bpy.types.Operator):
    bl_label = 'EI Add Morphing Components'
    bl_idname = 'object.addmorphcomp'
    bl_description = 'Copy selected objects as morphing component'

    def execute(self, context):
        # prefix = bpy.context.scene.morph_comp

        def addMorphComp(prefix):
            links = dict()
            childs = dict()
            clear_unlinked_data()
            scene = bpy.context.scene

            def get_true_name(name: str):
                return name[2:] if name[0:2] in MODEL().morph_comp.values() else name

            col_num = list(MODEL().morph_comp.keys())[list(MODEL().morph_comp.values()).index(prefix)]
            if col_num > 0:
                previous_col_name = MODEL().morph_collection[col_num - 1]
                if previous_col_name not in scene.collection.children:
                    self.report({'ERROR'}, 'Previous collection \"' + previous_col_name + '\" does not exist')
                    return {'CANCELLED'}

            bExist = False
            collections = bpy.context.scene.collection.children
            for obj in bpy.context.selected_objects:

                # save links
                # if obj in bpy.data.objects:

                for objs in bpy.context.scene.collection.children['base'].objects:
                    if objs.parent is None:
                        links[prefix + get_true_name(objs.name)] = None
                    else:
                        links[prefix + get_true_name(objs.name)] = (prefix + get_true_name(objs.parent.name))

                #                if obj.child is None:
                #                    childs[prefix + true_name] = None
                #                else:
                #                    childs[prefix + true_name] = (prefix + get_true_name(obj.parent.name))

                # Сохраняем чайлдов у объекта
                # coll_name = model().morph_collection[col_num]
                # for obj in collections[col_num].objects:
                #    if obj.parent is (prefix + true_name):
                #        childs.add(obj.name)
                #        print(prefix + true_name + ' have child ' + obj.name)

                # Заменяем или ругаемся про существующий объект в целевой коллекции
                true_name = get_true_name(obj.name)
                if (prefix + true_name) in bpy.data.objects:
                    bReplace = bpy.context.scene.auto_replace
                    if not bReplace:
                        print(obj.name + ' already have this morph comp')
                        bExist = True
                        continue
                    else:
                        bpy.data.objects.remove(bpy.data.objects[prefix + true_name])

                        # coll = scene.collection.children[coll_name]
                # del_name = obj.name
                ##if (model().morph_comp[col_num] + obj.name) in coll.objects:
                # self.report({'INFO'}, 'Старые модели удалены/ old models deleted')
                # bpy.data.objects.remove(bpy.data.objects[del_name])

                # create copy of object
                new_obj = obj.copy()
                new_obj.name = prefix + true_name
                new_obj.data = obj.data.copy()
                new_obj.data.name = new_obj.name

                coll_name = MODEL().morph_collection[
                    list(MODEL().morph_comp.keys())[list(MODEL().morph_comp.values()).index(prefix)]]
                if coll_name not in scene.collection.children:
                    new_col = bpy.data.collections.new(coll_name)
                    scene.collection.children.link(new_col)
                coll = scene.collection.children[coll_name]
                coll.objects.link(new_obj)
                new_obj.select_set(False)

            if not links:
                self.report({'ERROR'},
                            'Object(s) already have these morph components' if bExist else 'Empty objects to copy. Please select objects')
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
        # prefix = bpy.context.scene.morph_comp

        def addMorphComp(prefix):

            links = dict()
            childs = dict()
            clear_unlinked_data()
            scene = bpy.context.scene

            newname = scene.figcopy_name
            newparent = scene.figcopy_parent

            def get_true_name(name: str):
                return name[2:] if name[0:2] in MODEL().morph_comp.values() else name

            col_num = list(MODEL().morph_comp.keys())[list(MODEL().morph_comp.values()).index(prefix)]
            if col_num > 0:
                previous_col_name = MODEL().morph_collection[col_num - 1]
                if previous_col_name not in scene.collection.children:
                    self.report({'ERROR'}, 'Previous collection \"' + previous_col_name + '\" does not exist')
                    return {'CANCELLED'}

            bExist = False
            collections = bpy.context.scene.collection.children
            for obj in bpy.context.selected_objects:

                # save links
                # if obj in bpy.data.objects:

                for objs in collections['base'].objects:
                    if objs.parent is None:
                        links[prefix + get_true_name(objs.name)] = None
                    else:
                        links[prefix + get_true_name(objs.name)] = (prefix + get_true_name(objs.parent.name))

                #                if obj.child is None:
                #                    childs[prefix + true_name] = None
                #                else:
                #                    childs[prefix + true_name] = (prefix + get_true_name(obj.parent.name))

                # Сохраняем чайлдов у объекта
                # coll_name = model().morph_collection[col_num]
                # for obj in collections[col_num].objects:
                #    if obj.parent is (prefix + true_name):
                #        childs.add(obj.name)
                #        print(prefix + true_name + ' have child ' + obj.name)

                # Заменяем или ругаемся про существующий объект в целевой коллекции
                true_name = get_true_name(obj.name)
                true_namenew = get_true_name(newname)
                # if (prefix + true_name) in bpy.data.objects:
                if (prefix + true_namenew) in bpy.data.objects:
                    bReplace = bpy.context.scene.auto_replace
                    if not bReplace:
                        print(obj.name + ' already have this morph comp')
                        bExist = True
                        continue
                    else:
                        bpy.data.objects.remove(bpy.data.objects[prefix + true_namenew])

                        # coll = scene.collection.children[coll_name]
                # del_name = obj.name
                ##if (model().morph_comp[col_num] + obj.name) in coll.objects:
                # self.report({'INFO'}, 'Старые модели удалены/ old models deleted')
                # bpy.data.objects.remove(bpy.data.objects[del_name])

                # create copy of object
                new_obj = obj.copy()
                # new_obj.name = prefix + true_name
                new_obj.name = prefix + newname
                new_obj.data = obj.data.copy()
                new_obj.data.name = new_obj.name

                for parents in bpy.data.objects:
                    # self.report({'INFO'}, str(get_true_name(parents.name)) + newparent)
                    for obj in bpy.context.selected_objects:
                        # self.report({'INFO'}, prefix + (get_true_name(parents.name)) )
                        if (str(get_true_name(parents.name))) == newparent:
                            self.report({'INFO'}, newparent)
                            resu = bpy.data.objects[(prefix + get_true_name(parents.name))]
                            bpy.data.objects[new_obj.name].parent = resu

                coll_name = MODEL().morph_collection[
                    list(MODEL().morph_comp.keys())[list(MODEL().morph_comp.values()).index(prefix)]]
                if coll_name not in scene.collection.children:
                    new_col = bpy.data.collections.new(coll_name)
                    scene.collection.children.link(new_col)
                coll = scene.collection.children[coll_name]
                coll.objects.link(new_obj)
                new_obj.select_set(False)

            if not links:
                self.report({'ERROR'},
                            'Object(s) already have these morph components' if bExist else 'Empty objects to copy. Please select objects')
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

        def get_true_name(name: str):
            return name[2:] if name[0:2] in MODEL().morph_comp.values() else name

        col_num = list(MODEL().morph_comp.keys())[list(MODEL().morph_comp.values()).index(prefix)]
        if col_num > 0:
            previous_col_name = MODEL().morph_collection[col_num - 1]
            if previous_col_name not in scene.collection.children:
                self.report({'ERROR'}, 'Previous collection \"' + previous_col_name + '\" does not exist')
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

            coll_name = MODEL().morph_collection[
                list(MODEL().morph_comp.keys())[list(MODEL().morph_comp.values()).index(prefix)]]
            if coll_name not in scene.collection.children:
                new_col = bpy.data.collections.new(coll_name)
                scene.collection.children.link(new_col)
            coll = scene.collection.children[coll_name]
            coll.objects.link(new_obj)
            new_obj.select_set(False)

        if not links:
            self.report({'ERROR'},
                        'Object(s) already have these morph components' if bExist else 'Empty objects to copy. Please select objects')
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
        if collections[0].name != MODEL().morph_collection[0]:
            self.report({'ERROR'}, 'Base collection must be named as \"base\"')
            return {'CANCELLED'}

        MODEL().name = bpy.context.scene.figmodel_name
        if not MODEL().name:
            self.report({'ERROR'}, 'Model name is empty')
            return {'CANCELLED'}

        item = fig_utils.CItemGroupContainer.get_item_group(MODEL().name)
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
                coll_name = MODEL().morph_collection[i]
                if coll_name not in scene.collection.children:
                    new_col = bpy.data.collections.new(coll_name)
                    scene.collection.children.link(new_col)
                coll = scene.collection.children[coll_name]
                morph_name = MODEL().morph_comp[i]
                if morph_name in coll.objects:
                    continue

                # detect suitable obj
                new_obj: bpy.types.Object = obj.copy()
                new_obj.name = MODEL().morph_comp[i] + obj.name
                new_obj.data = obj.data.copy()
                new_obj.data.name = new_obj.name
                coll.objects.link(new_obj)
                new_obj.select_set(False)

            for i in range(1, 8):
                for child, parent in links.items():
                    if parent is None:
                        continue
                    bpy.data.objects[MODEL().morph_comp[i] + child].parent = bpy.data.objects[
                        MODEL().morph_comp[i] + parent]

        return {'FINISHED'}


class CAutoFillMorphNew_OP_Operator(bpy.types.Operator):
    bl_label = 'Create morphs for %s meshes'
    bl_idname = 'object.automorphnew'
    bl_description = 'Generates morph components for existing "base" collection.\n' \
                     'NOTE: applies R&S transforms to base collection ' \
                     'which may break animation or model parent-child positioning'

    mesh_mask: bpy.props.StringProperty(name="Mesh mask", default="",
                                        description="Comma-separated include list of mesh names")

    get_name = classmethod(get_name)

    def execute(self, context):
        collections = bpy.data.collections
        self.report({'INFO'}, 'Executing create all morphs')
        base_coll = collections.get("base")
        if not base_coll:
            self.report({'ERROR'}, 'No base collection')
            return {'CANCELLED'}

        MODEL().name = bpy.context.scene.figmodel_name
        if not MODEL().name:
            self.report({'ERROR'}, 'Model name is empty')
            return {'CANCELLED'}

        item = fig_utils.CItemGroupContainer.get_item_group(MODEL().name)
        obj_count = item.morph_component_count
        if obj_count == 1:
            self.report({'INFO'}, 'This object type has only 1 collection \"base\"')
            return {'CANCELLED'}

        mesh_mask = self.mesh_mask
        mesh_mask_set = set(map(str.strip, mesh_mask.split(','))) if mesh_mask else None

        reload_modules()
        scene_utils.clear_unlinked_data()
        res, duration = call_with_time(lambda: scene_utils.create_all_morphs(context, mesh_mask_set))
        self.report({'INFO'}, f'Done in {duration:.2f}')
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
            # local_pos = mwi * ob_b.matrix_world.translation
            local_pos = mwi @ ob_b.matrix_world.Identity(4).translation
            # local_pos = mwi @ ob_b.location
            # local_pos = mwi @ ob_b.matrix_world.Identity(4).location
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
        if collections[0].name != MODEL().morph_collection[0]:
            self.report({'ERROR'}, 'Base collection must be named as \"base\"')
            return {'CANCELLED'}

        MODEL().name = bpy.context.scene.figmodel_name
        if not MODEL().name:
            self.report({'ERROR'}, 'Model name is empty')
            return {'CANCELLED'}

        item = fig_utils.CItemGroupContainer.get_item_group(MODEL().name)
        obj_count = item.morph_component_count
        if obj_count == 1:
            self.report({'INFO'}, 'This object type has only 1 collection \"base\"')
            return {'CANCELLED'}

        def get_true_name(name: str):
            return name[2:] if name[0:2] in MODEL().morph_comp.values() else name

        clear_unlinked_data()
        scene = bpy.context.scene
        links = dict()
        # Триангулируем и применяем модификаторы на базовой модели
        bAutofix = bpy.context.scene.auto_apply
        if bAutofix:
            scene_utils.auto_fix_scene()

        scn = scene
        scaled = scn.scaled
        # удаляем старые модели
        for obj in collections[0].objects:
            if obj.type != 'MESH':
                continue
            for i in range(4, 8):
                if len(collections) == 1:
                    continue
                coll_name = MODEL().morph_collection[i]
                for obj in collections[i].objects:
                    if obj.type != 'MESH':
                        continue
                    coll = scene.collection.children[coll_name]
                    del_name = obj.name
                    # if (model().morph_comp[i] + obj.name) in coll.objects:
                    self.report({'INFO'}, 'Старые модели удалены/ old models deleted')
                    bpy.data.objects.remove(bpy.data.objects[del_name])

        for mc in range(0, 4):
            for obj in collections[mc].objects:
                if obj.type != 'MESH':
                    continue
                links[obj.name] = None if obj.parent is None else obj.parent.name
                # добавляем коллекции
                # for i in range(4, 7):
                coll_name = MODEL().morph_collection[mc + 4]
                if coll_name not in scene.collection.children:
                    new_col = bpy.data.collections.new(coll_name)
                    scene.collection.children.link(new_col)

                coll = scene.collection.children[coll_name]
                morph_name = MODEL().morph_comp[mc + 4]
                # if morph_name in coll.objects:
                #    continue
                # копируем меши
                # detect suitable obj
                new_obj = obj.copy()
                new_obj.name = MODEL().morph_comp[mc + 4] + get_true_name(obj.name)
                new_obj.data = obj.data.copy()
                new_obj.data.name = new_obj.name
                coll.objects.link(new_obj)
                new_obj.select_set(False)
            # привязываем родителей
            # for c in range(4, 7):
            for obj in collections[mc + 4].objects:
                for child, parent in links.items():
                    if parent is None:
                        continue
                    bpy.data.objects[MODEL().morph_comp[mc + 4] + get_true_name(child)].parent = bpy.data.objects[
                        MODEL().morph_comp[mc + 4] + get_true_name(parent)]
            for obj in bpy.context.selected_objects:
                obj.select_set(False)
            # Трогаем только scaled коллекции
            # for s in range(4, 7):
            for obj in collections[mc + 4].objects:
                for child, parent in links.items():
                    if parent is None:
                        # continue
                        bpy.data.objects[MODEL().morph_comp[mc + 4] + get_true_name(child)].scale = (
                            scaled, scaled, scaled)

            for obj in bpy.context.selected_objects:
                obj.select_set(False)
            for obj in bpy.data.objects:
                # Применяем все трансформации
                obj.select_set(True)
                bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
                # for obj in bpy.context.selected_objects:
                obj.select_set(False)

        return {'FINISHED'}


class CRepackResFile(bpy.types.Operator):
    bl_label = 'Optimize RES'
    bl_idname = 'object.repack_resfile'
    bl_description = 'Recursively repack .res archive, reducing file size'

    def execute(self, context):
        res_file = context.scene.res_file
        reload_modules()
        scene_utils.repack_resfile(res_file)
        return {'FINISHED'}


def populate_lists(context: bpy.types.Context):
    populate_model_list(context)
    populate_animation_list(context)


def populate_model_list(context: bpy.types.Context):
    res_path = context.scene.res_file
    scene = context.scene
    res = ResFile(res_path)
    bpy.context.scene.model_list.clear()
    files = res.get_model_list()
    for file in files:
        item = scene.model_list.add()
        item.name = file


def populate_animation_list(context: bpy.types.Context):
    scene = context.scene
    res_path = scene.res_file
    res = ResFile(res_path)
    scene.animation_list.clear()
    model_name = scene.figmodel_name
    try:
        files = res.get_animation_list(model_name + ".anm")
        print('anims', files)
    except KeyError as e:
        print(e)
        files = []
    for file in files:
        item = scene.animation_list.add()
        item.name = file


class CSelectResFileIndex(bpy.types.Operator):
    bl_label = 'Select RES'
    bl_idname = 'object.select_resfile'
    bl_description = 'Select this res file'

    res_file_index: bpy.props.IntProperty(default=0, options={'HIDDEN'}, )

    def execute(self, context):
        context.scene.res_file = scene_utils.get_res_file_buffer(self.res_file_index)
        populate_lists(context)
        return {'FINISHED'}


class CChooseResFile(bpy.types.Operator, ImportHelper):
    '''
    Operator to choose *.res file
    '''
    bl_label = 'Choose Resfile'
    bl_idname = 'object.choose_resfile'
    bl_description = ('*.res file containing models, figures, animations, usually figures.res.\n'
                      ' Click [...] then [ ✓ ] to select.')

    filename_ext = ".res"

    filter_glob: bpy.props.StringProperty(default="*.res", options={'HIDDEN'}, maxlen=255,
                                          # Max internal buffer length, longer would be clamped.
                                          )

    res_file_index: bpy.props.IntProperty(default=0, options={'HIDDEN'}, )

    def execute(self, context):
        scene_utils.set_res_file_buffer(self.res_file_index, self.filepath)
        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        wm.fileselect_add(self)
        return {'RUNNING_MODAL'}


class CClearScene(bpy.types.Operator):
    bl_label = 'Clear scene'
    bl_idname = 'object.clear_scene'
    bl_description = 'Should be pretty obvious'

    def execute(self, context: bpy.types.Context) -> set[str]:
        bpy.context.window_manager.progress_begin(0, 99)
        _, duration = call_with_time(lambda: scene_utils.scene_clear())
        bpy.context.window_manager.progress_end()
        self.report({'INFO'}, f'Done in {duration:.2f} sec')
        return {'FINISHED'}


class CModelSelect(bpy.types.Operator):
    bl_label = 'Select model'
    bl_idname = 'object.model_select'
    bl_description = 'Select model name'

    model_name: bpy.props.StringProperty(name="Model name", default="", options={"HIDDEN"})

    def execute(self, context):
        scene = context.scene
        scene.figmodel_name = self.model_name
        populate_animation_list(context)
        return {'FINISHED'}


class CAnimationSelect(bpy.types.Operator):
    bl_label = 'Select animation'
    bl_idname = 'object.animation_select'
    bl_description = 'Select animation name'

    animation_name: bpy.props.StringProperty(name="Model name", default="", options={"HIDDEN"})

    def execute(self, context):
        scene = context.scene
        scene.animation_name = self.animation_name
        return {'FINISHED'}


class CModelImport(bpy.types.Operator):
    name_short = "Import"
    bl_label = 'Import %s meshes'
    bl_idname = 'object.model_import'
    bl_description = 'Import model/figure from selected RES into "base" collection.'
    mesh_mask: bpy.props.StringProperty(name="Mesh mask", default="",
                                        description="Comma-separated include list of mesh names")
    model_name: bpy.props.StringProperty(default="")
    get_name = classmethod(get_name)

    def null_result(self, res, model_name):
        item_list = res.get_model_list()
        self.report({'ERROR'}, 'Cannot find model %s.\nItems list:%s' % (model_name, item_list))
        return {'CANCELLED'}

    @classmethod
    def get_model_name(cls, context):
        scene = context.scene
        model_name = scene.figmodel_name
        return model_name

    def execute(self, context):
        self.report({'INFO'}, 'Executing import model')

        res_path = bpy.context.scene.res_file
        if not res_path or not os.path.exists(res_path):
            self.report({'ERROR'}, _('RES file not found at: %s') % res_path)
            return {'CANCELLED'}

        reload_modules()
        res = ResFile(res_path)
        model_name = self.model_name or self.get_model_name(context)
        if not model_name:
            self.report({'ERROR'}, 'Model/Figure name is empty')
            return self.null_result(res, model_name)

        mesh_mask = self.mesh_mask
        mesh_mask_set = set(map(str.strip, mesh_mask.split(','))) if mesh_mask else None

        bpy.context.window_manager.progress_begin(0, 99)
        func = lambda: scene_utils.import_model(context, res, model_name, mesh_mask_set)
        result, duration = call_with_time(func)
        bpy.context.window_manager.progress_end()

        if result is None:
            return self.null_result(res, model_name)

        self.report({'INFO'}, f'Done in {duration:.2f} sec')
        return {'FINISHED'}


class CModelExport(bpy.types.Operator):
    bl_label = 'Export %s meshes'
    bl_idname = 'object.model_export'
    bl_description = (
        "Export models in base/morph collections into selected RES file, Evil Islands format (not Etherlords).\n"
        "NOTE: Export needs all eight morph collections in the scene.\n"
        "NOTE: Morphing/shapekey (in original dragon/bat wings) animations run on top of base model\n")

    mesh_mask: bpy.props.StringProperty(name="Mesh mask", default="",
                                        description="Comma-separated include list of mesh names")
    model_name: bpy.props.StringProperty(default="")
    get_name = classmethod(get_name)

    @classmethod
    def get_model_name(cls, context):
        scene = context.scene
        model_name = scene.figmodel_name
        return model_name

    def execute(self, context):
        self.report({'INFO'}, 'Executing export')
        res_path = bpy.context.scene.res_file
        if not res_path:
            self.report({'ERROR'}, 'res file empty')
            return {'CANCELLED'}

        reload_modules()

        model_name = self.model_name or self.get_model_name(context)
        if not model_name:
            self.report({'ERROR'}, 'Model/Figure name is empty')
            return {'CANCELLED'}

        bAutofix = bpy.context.scene.auto_fix
        if bAutofix:
            scene_utils.auto_fix_scene()

        if not scene_utils.is_model_correct(model_name):
            self.report({'ERROR'},
                        'Model/Figure cannot pass check. \nSee System Console (Window->Toggle System Console)')
            return {'CANCELLED'}

        mesh_mask = self.mesh_mask
        mesh_mask_set = set(map(str.strip, mesh_mask.split(','))) if mesh_mask else None
        func = lambda: scene_utils.export_model(context, res_path, model_name, mesh_mask_set)
        bpy.context.window_manager.progress_begin(0, 99)
        res, duration = call_with_time(func)

        warn = ''
        if res:
            warn = "WARNING: meshes skipped! Check console"
            import pprint
            without_morphs = pprint.pformat(res)
            self.report({'WARNING'}, f'Meshes {without_morphs} are without morphs - export skipped')
        bpy.context.window_manager.progress_end()

        report_style = "WARNING" if warn else "INFO"
        self.report({report_style}, f'Done in {duration:.2f} sec. {warn}')
        return {'FINISHED'}


class CAnimationImport(bpy.types.Operator):
    bl_label = 'Import animation into %s collection'
    bl_idname = 'object.animation_import'
    bl_description = 'Import animation and animate meshes in base collection, or its copy with new name'

    animation_name: bpy.props.StringProperty(default="")
    target_collection: bpy.props.StringProperty(default="base", options={'HIDDEN'}, maxlen=255, )

    @classmethod
    def get_name(cls):
        context = bpy.context
        use_collection = context.scene.animation_name if context.scene.is_animation_to_new_collection else "base"
        name = _(cls.bl_label) % use_collection
        return name

    @classmethod
    def get_target_collection(cls, context):
        scene = context.scene
        collection = scene.animation_name if scene.is_animation_to_new_collection else "base"
        return collection

    def execute(self, context):
        self.report({'INFO'}, 'Executing animation import')
        scene = context.scene

        res_path = scene.res_file
        if not res_path or not os.path.exists(res_path):
            self.report({'ERROR'}, 'Res file not found at:' + res_path)
            return {'CANCELLED'}

        reload_modules()
        anm_name = self.animation_name or scene.animation_name
        model_name = scene.figmodel_name
        res_file = ResFile(res_path)

        if not model_name:
            self.report({'ERROR'}, 'Model/Figure name is empty')
            return {'CANCELLED'}

        # choosing model to load
        if model_name + '.anm' not in res_file.get_filename_list():
            self.report({'ERROR'}, 'Animations set for ' + model_name + 'not found')
            return {'CANCELLED'}

        animations = res_file.get_animation_list(model_name + ".anm")

        if not anm_name:
            self.report({'ERROR'}, 'Animation name is empty')

        if anm_name not in animations:  # set of animations
            self.report({'ERROR'}, 'Cannot find ' + anm_name + '\nAnimation list: ' + str(animations))
            return {'CANCELLED'}

        if not scene_utils.get_collection("base"):
            self.report({'ERROR'}, 'No base collection exists in the scene.')
            return {'CANCELLED'}

        # fix names for base collection being imported
        animation_destination_name = self.get_target_collection(context)
        self.report({'INFO'}, f'Importing into "{animation_destination_name}" collection')

        if animation_destination_name != "base":
            scene_utils.copy_collection("base", animation_destination_name)
            self.report({'INFO'}, f'Copying "base" collection as "{animation_destination_name}"')

        reload_modules()
        self.report({'INFO'}, f'Renaming .001-like names for "{animation_destination_name}"')

        def do_import():
            scene_utils.rename_drop_postfix(scene_utils.get_collection(animation_destination_name).objects)
            animations = scene_utils.read_animations(res_file, model_name, anm_name)
            links = scene_utils.collect_links(animation_destination_name)
            scene_utils.ei2abs_rotations(links, animations)

            bAutofix = bpy.context.scene.animsubfix
            if not bAutofix:
                scene_utils.abs2Blender_rotations(links, animations)

            scene_utils.insert_animation(animation_destination_name, animations)
            context.scene.frame_set(0)

        _, duration = call_with_time(do_import)

        self.report({'INFO'}, f'Done in {duration:.2f} sec')
        return {'FINISHED'}


class CAnimationExport(bpy.types.Operator):
    bl_label = 'Export animation from %s collection'
    bl_idname = 'object.animation_export'
    bl_description = ('Export animation in Evil islands format.\n'
                      'NOTE: Morphing/shapekey (in original dragon/bat wings) animations run on top of base model\n'
                      'May want to keep their morphs identical to base')

    target_collection: bpy.props.StringProperty(default=None, options={'HIDDEN'}, maxlen=255, )

    @classmethod
    def get_target_collection(cls, context):
        scene = context.scene
        collection = scene.animation_name if scene.is_animation_to_new_collection else "base"
        return collection

    def execute(self, context):
        self.report({'INFO'}, 'Executing animation export')

        scene = context.scene
        res_path = scene.res_file
        if not res_path or not os.path.exists(res_path):
            self.report({'ERROR'}, 'Res file not found at:' + res_path)
            return {'CANCELLED'}

        anm_name = self.animation_name or scene.animation_name
        model_name = scene.figmodel_name
        # resFile = ResFile(res_path)

        if not model_name:
            self.report({'ERROR'}, 'Model/Figure name is empty')
            return {'CANCELLED'}

        if not anm_name:
            self.report({'ERROR'}, 'Animation name is empty')
            return {'CANCELLED'}

        reload_modules()
        # fix names for collection being exported
        animation_source_name = self.target_collection or self.get_target_collection(context)
        self.report({'INFO'}, f'Exporting from "{animation_source_name}" collection')
        self.report({'INFO'}, f'Renaming .001-like names for "{animation_source_name}"')
        scene_utils.rename_drop_postfix(scene_utils.get_collection(animation_source_name).objects)

        is_use_mesh_frame_range = context.scene.is_use_mesh_frame_range
        self.report({'INFO'}, f'Use mesh frame range: {is_use_mesh_frame_range}')
        if is_use_mesh_frame_range:
            frame_range = scene_utils.get_collection_frame_range(animation_source_name)
        else:
            frame_range = context.scene.frame_start, context.scene.frame_end

        self.report({'INFO'}, f'Exporting frames from {frame_range[0]} to {frame_range[1]}')
        _, duration = call_with_time(
            lambda: scene_utils.export_animation(context, frame_range, animation_source_name, res_path))

        self.report({'INFO'}, f'Done in {duration:.2f} sec')
        return {'FINISHED'}


class CAnimation_OP_shapekey(bpy.types.Operator):
    bl_label = 'Animation to shapekeys'
    bl_idname = 'object.animation_shapekey'
    bl_description = "Select SRC and DEST (the square-highlighted one)\n" \
                     "Action will transfer SRC's vertex animation to DEST's shapekey animation"

    def execute(self, context):
        reload_modules()
        donor, acceptor = scene_utils.get_donor_acceptor(context)
        self.report({'INFO'}, f'Executing animation shapekeying from {donor.name} into {acceptor.name}')
        scene_utils.animation_to_shapekey(context, donor, acceptor)

        self.report({'INFO'}, 'Done')
        return {'FINISHED'}


class CAnimation_OP_BakeTransform(bpy.types.Operator):
    bl_label = 'Bake transform'
    bl_idname = 'object.animation_bake_transform'
    bl_description = 'For each object in selection, moves location / rotation / scale animation into shapekeys.\n' \
                     'Ignores objects with shapekeys (morph animation)'

    def execute(self, context):
        self.report({'INFO'}, 'Executing bake transform')
        # NOTE: context.selected_objects doesn't include invisible objects...
        selected = context.view_layer.objects.selected
        # selected = context.selected_objects

        if not selected:
            self.report({'ERROR'}, 'No object selected')
            return {"CANCELLED"}

        reload_modules()
        _, duration = call_with_time(lambda: scene_utils.bake_transform_animation(context))

        self.report({'INFO'}, f'Done in {duration:.2f} sec')
        return {'FINISHED'}


class CAnimation_OP_UE4_Toolchain(bpy.types.Operator):
    bl_label = 'UE4 to shapekeys'
    bl_idname = 'object.ue4_toolchain'
    bl_description = 'Transform UE4 skeleton-animated model into shapekeyed mesh\n' \
                     'Operates on root->armature->mesh structure, with root selected.'

    def execute(self, context):
        self.report({'INFO'}, f'Executing UE4 to EI')
        reload_modules()
        scene_utils.ue4_toolchain(self, context)
        self.report({'INFO'}, f'Done')
        return {'FINISHED'}


class CRenameDropPostfix_OP_operator(bpy.types.Operator):
    bl_label = 'Drop .001 name part'
    bl_idname = 'object.rename_drop_postfix'
    bl_description = 'Removes dot-numeric part from <*>.001 names to just <*>'

    def execute(self, context):
        self.report({'INFO'}, 'Executing rename - drop postifx')
        # NOTE: context.selected_objects doesn't include invisible objects...
        selected = context.view_layer.objects.selected
        if not selected:
            self.report({'ERROR'}, 'No object selected')
            return {"CANCELLED"}
        scene_utils.rename_drop_postfix(selected)
        self.report({'INFO'}, 'Done!')
        return {"FINISHED"}


# Define the custom operator
class CDebugTestOperator(bpy.types.Operator):
    bl_label = "Debug / Test"
    bl_idname = "object.debug_test"
    bl_description = "Do debug stuff"

    def execute(self, context):
        # tbd

        return {'FINISHED'}
