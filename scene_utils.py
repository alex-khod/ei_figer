# Copyright (c) 2022 konstvest
import typing

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
import bmesh
import copy
import io
from math import sqrt
from mathutils import Quaternion, Vector, Matrix
import copy as cp
import collections as py_collections
from typing import Set

from . utils import subVector, sumVector, CItemGroupContainer, CItemGroup, mulVector, sumVector
from . bone import CBone
from . figure import CFigure
from . resfile import ResFile
from . scene_management import CModel, CAnimations
from . animation import CAnimation
from . links import CLink

def model() -> CModel:
    return bpy.context.scene.model

def get_collection(collection_name = "base") -> bpy.types.Collection:
    collection = bpy.data.collections.get(collection_name)
    return collection

def rename_serial(old_obj, name):
    count = 1
    rename_old = f"{name}.{count:03d}"
    while rename_old in bpy.data.objects:
        count += 1
        rename_old = f"{name}.{count:03d}"
    old_obj.name = rename_old

def rename_drop_postfix(objects):
    for obj in objects:
        name = obj.name.rsplit('.')[0]

        if name in bpy.data.objects:
            rename_serial(bpy.data.objects.get(name), name)
        obj.name = name

def read_links(lnk_res : ResFile, lnk_name : str):
    with lnk_res.open(lnk_name) as lnk_res:
        data = lnk_res.read()
        lnk = CLink()
        lnk.read_lnk(data)
    return lnk

from . utils import CByteReader, unpack_uv, pack_uv, pack, unpack, \
    read_x, read_xy, read_xyz, read_xyzw, write_xy, write_xyz, write_xyzw, \
    get_uv_convert_count

def read_figure(fig_res : ResFile, fig_name : str):
    active_model : CModel = bpy.types.Scene.model
    err = 0
    with fig_res.open(fig_name) as fig_res:
        data = fig_res.read()
        fig = CFigure()
        err += fig.read_fig(fig_name, data)
        active_model.mesh_list.append(fig)
        #bon = CBone()
        #err += bon.read_bonvec(fig_name, [1,1,1])
        #active_model.pos_list.append(bon)
        #bpy.context.scene.cursor.location = (1,1,1)
        #bpy.context.scene.tool_settings.transform_pivot_point
    return err
    
def read_figSignature(resFile : ResFile, model_name):
    with resFile.open(model_name + '.mod') as meshes_container:
        mesh_list_res = ResFile(meshes_container)
        for fig_name in mesh_list_res.get_filename_list():
            active_model : CModel = bpy.types.Scene.model
            print(' fig_name for signature: ' + fig_name)
            with fig_res.open(fig_name) as fig_res:
                data = fig_res.read()
                fig = CFigure()
            
                parser = CByteReader(data)
                signature = parser.read('ssss').decode()
                if signature == 'FIG8':
                    return 8
                else:
                    return 1

def read_bone(bon_res : ResFile, bon_name : str):
    active_model : CModel = bpy.types.Scene.model
    err = 0
    with bon_res.open(bon_name) as bon_res:
        data = bon_res.read()
        bon = CBone()
        err += bon.read_bon(bon_name, data)
        active_model.pos_list.append(bon)
    return err

def read_model(resFile : ResFile, model_name, include_meshes=None):
    with resFile.open(model_name + '.mod') as meshes_container:
        mesh_list_res = ResFile(meshes_container)
        links_name = model_name
        links = read_links(mesh_list_res, links_name)
        filenames = mesh_list_res.get_filename_list()
        for mesh_name in filenames:
            if mesh_name == links_name:
                continue
            if include_meshes and mesh_name not in include_meshes:
                continue
            read_figure(mesh_list_res, mesh_name)
        return links

def read_bones(resFile : ResFile, model_name):
    err = 0
    #bones container
    with resFile.open(model_name + '.bon') as bone_container:
        bone_list_res = ResFile(bone_container)
        for bone_name in bone_list_res.get_filename_list():
            err += read_bone(bone_list_res, bone_name)
    return err

def read_animations(resFile : ResFile, model_name : str, animation_name : str) -> CAnimations:
    anm_list = []
    with resFile.open(model_name + '.anm') as animation_container:
        anm_res_file = ResFile(animation_container)
        with anm_res_file.open(animation_name) as animation_file:
            animation_res = ResFile(animation_file)
            for part_name in animation_res.get_filename_list(): #set of parts
                with animation_res.open(part_name) as part_res:
                    part = part_res.read()
                    anm = CAnimation()
                    anm.read_anm(part_name, part)
                    anm_list.append(anm)
    return CAnimations(anm_list)

def ensure_morph_collections():
    active_model: CModel = bpy.types.Scene.model
    for collection_name in active_model.morph_collection:
        if collection_name not in bpy.data.collections:
            collection = bpy.data.collections.new(collection_name)
            bpy.context.scene.collection.children.link(collection)

def import_mod_file(res_file, model_name, include_meshes=None):
    print("reading mod")
    active_model: CModel = bpy.types.Scene.model
    active_model.reset('fig')
    active_model.name = model_name

    links = read_model(res_file, model_name, include_meshes)
    #            if read_figSignature(resFile, model_name) == 8:          ##LostSoul
    bEtherlord = bpy.context.scene.ether
    if not bEtherlord:
        read_bones(res_file, model_name)
    #                break
    container = CItemGroupContainer()
    item_group = container.get_item_group(active_model.name)
    ensure_morph_collections()
    for fig in active_model.mesh_list:
        create_mesh_2(fig, item_group)
    create_links_2(links, item_group.morph_component_count)
    for bone in active_model.pos_list:
        set_pos_2(bone, container)

def import_lnk_fig_bon_files(res_file, model_name, include_meshes=None):
    print("reading lnk")
    active_model: CModel = bpy.types.Scene.model
    active_model.reset('fig')
    active_model.name = model_name

    model_links: CLink = read_links(res_file, model_name + '.lnk')
    renamed_dict = dict()
    for part, parent in model_links.links.items():
        if parent is None:
            renamed_dict[active_model.name + part] = None
        else:
            renamed_dict[active_model.name + part] = active_model.name + parent
    model_links.links = renamed_dict
    # read parts
    filenames = res_file.get_filename_list()
    for part in model_links.links.keys():
        if part not in include_meshes:
            continue
        if (part + '.fig') in filenames:
            read_figure(res_file, part + '.fig')
            nnn = (active_model.mesh_list[-1].name.split(model_name)[1]).rsplit('.')[0]  # TODO: nnn
            active_model.mesh_list[-1].name = nnn
        else:
            print(part + '.fig not found')
        if (part + '.bon') in filenames:
            read_bone(res_file, part + '.bon')
        else:
            print(part + '.bon not found')
    # RuntimeError('Stopping the script here')
    container = CItemGroupContainer()
    item_group = container.get_item_group(active_model.name)
    ensure_morph_collections()
    for fig in active_model.mesh_list:
        create_mesh_2(fig, item_group)

    create_links_2(model_links, item_group.morph_component_count)
    for bone in active_model.pos_list:
        set_pos_2(bone, container)


def import_model(context, res_file, model_name, include_meshes: Set[str]=None):
    if (model_name + '.mod') in res_file.get_filename_list():
        import_mod_file(res_file, model_name, include_meshes)
    elif (model_name + '.lnk') in res_file.get_filename_list():
        import_lnk_fig_bon_files(res_file, model_name)
    else:
        return None
    return True

def export_model(context, res_path, model_name, include_meshes=None):
    links = collect_links()

    active_model: CModel = bpy.types.Scene.model
    active_model.reset()
    active_model.name = model_name

    collect_pos(model_name, include_meshes)
    collect_mesh(include_meshes)

    obj_count = CItemGroupContainer().get_item_group(model().name).morph_component_count
    if obj_count == 1:  # save lnk,fig,bon into res (without model resfile)
        with ResFile(res_path, 'a') as res:
            with res.open(active_model.name + '.lnk', 'w') as file:
                data = links.write_lnk()
                file.write(data)
        # write figs
        with ResFile(res_path, 'a') as res:
            for mesh in active_model.mesh_list:
                mesh.name = model_name + mesh.name + '.fig'
                with res.open(mesh.name, 'w') as file:
                    data = mesh.write_fig()
                    file.write(data)
        # write bones
        with ResFile(res_path, 'a') as res:
            for bone in active_model.pos_list:
                bone.name = model_name + bone.name + '.bon'
                with res.open(bone.name, 'w') as file:
                    data = bone.write_bon()
                    file.write(data)
    else:
        # append data
        initial_model = {}
        initial_bone = {}
        if include_meshes:
            with ResFile(res_path, 'r') as res:
                with res.open(active_model.name + '.mod', 'r') as file:
                    with ResFile(file, 'r') as res2:
                        for file2 in res2.get_filename_list():
                            with res2.open(file2, 'r') as f2:
                                initial_model[file2] = f2.read()
                with res.open(active_model.name + '.bon', 'r') as file:
                    with ResFile(file, 'r') as res2:
                        for file2 in res2.get_filename_list():
                            with res2.open(file2, 'r') as f2:
                                initial_bone[file2] = f2.read()
        # prepare links + figures (.mod file)
        model_res = io.BytesIO()
        with ResFile(model_res, 'w') as res:
            for file2, data in initial_model.items():
                with res.open(file2, 'w') as file:
                    file.write(data)
            # write lnk
            with res.open(active_model.name, 'w') as file:
                data = links.write_lnk()
                file.write(data)
            # write meshes
            for part in active_model.mesh_list:
                with res.open(part.name, 'w') as file:
                    data = part.write_fig()
                    file.write(data)

        # prepare bons file (.bon file)
        bone_res = io.BytesIO()
        with ResFile(bone_res, 'w') as res:
            for file2, data in initial_bone.items():
                with res.open(file2, 'w') as file:
                    file.write(data)

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


def ei2abs_rotations(links: CLink, animations: CAnimations):
    """
    Calculates absolute rotations for parts in links, based on EI values
    """
    lnk = links.links
    #TODO: check if links correctly (None parent has only 1 obj and other)
    if not links:
        raise Exception("Error: empty links")

    def calc_frames(part : CAnimation):
        if lnk[part.name] is None: #root object
            part.abs_rotation = cp.deepcopy(part.rotations)
        else:
            parent_anm = animations.get_animation(lnk[part.name])
            print(lnk[part.name])
            if len(parent_anm.abs_rotation) == 0:
                calc_frames(parent_anm)
            part.abs_rotation = cp.deepcopy(parent_anm.abs_rotation)
            for i in range(len(part.rotations)):
                part.abs_rotation[i].rotate(part.rotations[i])

    for part in lnk.keys():
        anm = animations.get_animation(part)
        if anm is None:
            print('animation for ' + part + ' not found')
        else:
            calc_frames(anm)

def abs2ei_rotations(links: CLink, animations: CAnimations):
    lnk = links.links

    def calc_frames(part : CAnimation):
        if lnk[part.name] is None:
            return
        
        for i in range(len(part.rotations)):
            parent_rot = cp.deepcopy(animations.get_animation(lnk[part.name]).abs_rotation[i])
            parent_rot_invert = parent_rot.inverted().copy()
            parent_rot_invert.rotate(part.abs_rotation[i])
            part.rotations[i] = parent_rot_invert.copy()
    
    for part in lnk.keys():
        anm = animations.get_animation(part)
        if anm is None:
            print('animation for ' + part + ' not found')
        else:
            calc_frames(anm)

def abs2Blender_rotations(links: CLink, animations: CAnimations):
    """
    Calculates rotation from absolute to Blender
    """
    lnk = links.links

    def calc_frames(part : CAnimation):
        if lnk[part.name] is None:
            return
        
        for i in range(len(part.rotations)):
            parent_rot = cp.deepcopy(animations.get_animation(lnk[part.name]).abs_rotation[i])
            parent_rot_invert = parent_rot.inverted().copy()
            child_rot : Quaternion = parent_rot.copy()
            child_rot.rotate(part.rotations[i])
            part.rotations[i] = child_rot.copy()
            part.rotations[i].rotate(parent_rot_invert)
    
    for part in lnk.keys():
        anm = animations.get_animation(part)
        if anm is None:
            print('animation for ' + part + ' not found')
        else:
            calc_frames(anm)

def blender2abs_rotations(links: CLink, animations: CAnimations):
    lnk = links.links
    #TODO: check if links correctly (None parent has only 1 obj and other)
    if not links:
        raise Exception("Error: empty links")

    def calc_frames(part : CAnimation):
        if lnk[part.name] is None: #root object
            part.abs_rotation = cp.deepcopy(part.rotations)
        else:
            parent_anm = animations.get_animation(lnk[part.name])
            if len(parent_anm.abs_rotation) == 0:
                calc_frames(parent_anm)
            part.abs_rotation = cp.deepcopy(part.rotations)
            for i in range(len(part.rotations)):
                part.abs_rotation[i].rotate(parent_anm.abs_rotation[i])
    
    for part in lnk.keys():
        anm = animations.get_animation(part)
        if anm is None:
            print('animation for ' + part + ' not found')
        else:
            calc_frames(anm)

    return 0


def clear_old_morphs(start_index=1, include_meshes=None):
    # base_meshes = set([obj.name for obj in get_collection("base").objects])
    for coll_name, coll_prefix in zip(model().morph_collection[start_index:], model().morph_comp[start_index:]):
        coll = get_collection(coll_name)
        if not coll:
            continue
        for obj in coll.objects:
            # or (coll_prefix + obj.name) not in base_meshes:
            if (include_meshes and obj.name in include_meshes):
                bpy.data.objects.remove(obj)
    return True


def create_mesh_2(figure: CFigure, item_group: CItemGroup):
    # create mesh, replacing old in collection or renaming same-named mesh elsewhere
    active_model : CModel = bpy.context.scene.model
    faces = []
    ftemp = [0, 0, 0]
    face_indices_count = figure.header[3] - 2
    for i in range(0, face_indices_count, 3):
        for ind in range(3):
            ftemp[ind] = figure.v_c[figure.indicies[i + ind]][0]
        faces.append([ftemp[0], ftemp[1], ftemp[2]])

    bEtherlord = bpy.context.scene.ether
    if not bEtherlord:
        mesh_count = item_group.morph_component_count
    else:
        mesh_count = 1

    for mesh_num in range(mesh_count):
        collection_name = active_model.morph_collection[mesh_num]
        collection = get_collection(collection_name)
        name = active_model.morph_comp[mesh_num] + figure.name
        # remove old mesh
        old_obj_collection = collection.objects.get(name)
        if old_obj_collection:
            bpy.data.objects.remove(old_obj_collection)
        old_obj = bpy.data.objects.get(name)
        if old_obj:
            rename_serial(old_obj, name)
        # insert new mesh
        base_mesh = bpy.data.meshes.new(name=name)
        base_obj = bpy.data.objects.new(name, base_mesh)
        collection.objects.link(base_obj)
        base_obj.location = (0, 0, 0)
        base_mesh.from_pydata(figure.verts[mesh_num], [], faces)
        
        #TODO: create material
        print('meshname ' + name + ' is creating')
        base_mesh.uv_layers.new(name=bpy.context.scene.model.name)
        for uv_ind in range(figure.header[3]):
            for xy in range(2):
                base_mesh.uv_layers[0].data[uv_ind].uv[xy] = \
                        figure.t_coords[figure.v_c[figure.indicies[uv_ind]][1]][xy]
        print('meshname ' + name + ' created')
        base_mesh.update()
    
def set_pos_2(bone : CBone, container: CItemGroupContainer):
    active_model : CModel = bpy.context.scene.model
    item_group = container.get_item_group(bone.name)
    obj_count = item_group.morph_component_count
    
    for obj_num in range(obj_count):
        name = active_model.morph_comp[obj_num] + bone.name
        if name in bpy.data.objects:
            obj = bpy.data.objects[name]
            obj.location = bone.pos[obj_num]
    
    return 0

def create_links_2(link: CLink, obj_count=1):
    active_model: CModel = bpy.context.scene.model
    for part, parent in link.links.items():
        if parent is None:
            continue
        for obj_num in range(obj_count):
            part_name = active_model.morph_comp[obj_num] + part
            parent_name = active_model.morph_comp[obj_num] + parent
            if part_name in bpy.data.objects and parent_name in bpy.data.objects:
                bpy.data.objects[part_name].parent = bpy.data.objects[parent_name]
    
    return 0

def clear_animation_data(collection_name: str = "base"):
    base_rotation = Quaternion((1, 0, 0, 0))
    bpy.context.scene.frame_set(0)
    model : CModel = bpy.types.Scene.model

    collection = get_collection(collection_name)
    for obj in collection.objects:
        if model.is_morph_name(obj.name):
            continue
        obj.rotation_mode = 'QUATERNION'
        obj.animation_data_clear()
        obj.rotation_quaternion = base_rotation
        if obj.parent is None:
            obj.location = (0, 0, 0)
        obj.shape_key_clear()

    bpy.context.scene.frame_start = 1
    bpy.context.scene.frame_end = 250

def insert_keyframe(sk, f):
    sk.keyframe_insert("value", frame=f-1)
    sk.keyframe_insert("value", frame=f+1)
    sk.value = 1.0
    sk.keyframe_insert("value", frame=f)   

def insert_animation(to_collection : str, anm_list : CAnimations):
    if not bpy.data.collections.get("base"):
        raise Exception("No \"base\" collection exists!")
    if not bpy.data.collections.get(to_collection) and to_collection != "base":
        copy_collection("base", to_collection)

    rename_drop_postfix(get_collection(to_collection).objects)

    clear_animation_data(to_collection)

    for part in anm_list:
        if part.name not in bpy.data.objects:
            print('object ' + part.name + ' not found in animation list')
            continue

        obj = bpy.data.objects[part.name]
        obj.rotation_mode = 'QUATERNION'
        bpy.context.scene.frame_end = 0
        bpy.context.scene.frame_end = len(part.rotations)-1 #for example, 43 frames from 0 to 42
        for frame in range(len(part.rotations)):
            #rotations
            bpy.context.scene.frame_set(frame) #choose frame
            obj.rotation_quaternion = part.rotations[frame]
            obj.keyframe_insert(data_path='rotation_quaternion', index=-1)
            #positions
            bEtherlord = bpy.context.scene.ether
            if not bEtherlord:
                if obj.parent is None: #root
                    obj.location = part.translations[frame]
                    obj.keyframe_insert(data_path='location', index=-1)
            else:
                obj.location = part.translations[frame]
                obj.keyframe_insert(data_path='location', index=-1)
            
            #morphations
        if len(part.morphations) > 0:
            obj.shape_key_add(name='basis', from_mix=False)
            for frame in range(len(part.morphations)):
                key = obj.shape_key_add(name=str(frame), from_mix=False)
                for i in range(len(part.morphations[frame])):
                    key.data[i].co = sumVector(obj.data.vertices[i].co, part.morphations[frame][i])
                insert_keyframe(key, frame)
    return True

def get_res_file_buffer(index):
    return getattr(bpy.context.scene, 'res_file_buffer%d' % index)

def set_res_file_buffer(index, value):
    setattr(bpy.context.scene, 'res_file_buffer%d' % index, value)

def collect_animations(collection_name="base"):
    anm_list = []
    coll = get_collection(collection_name)
    for obj in coll.objects:
        if obj.name[0:2] in bpy.types.Scene.model.morph_comp.values():
            continue #skip morphed objects

        if obj.animation_data is None and (not obj.data.shape_keys):
            continue

        anm = CAnimation()
        anm.name = obj.name
        obj.rotation_mode = 'QUATERNION'
        
        for frame in range(bpy.context.scene.frame_start, bpy.context.scene.frame_end + 1):
            #rotations
            bpy.context.scene.frame_set(frame) #choose frame
            anm.rotations.append(Quaternion(obj.rotation_quaternion))
            #positions
            bEtherlord = bpy.context.scene.ether
            if not bEtherlord:
                print('object ' + anm.name + ' loc is ' + str(obj.location))
                if obj.parent is None: #root
                    anm.translations.append(obj.location.copy())
            else:
                anm.translations.append(obj.location.copy())

            #morphations
            if not obj.data.shape_keys:
                continue

            if not len(anm.morphations):
                anm.morphations = [[] for _ in range(bpy.context.scene.frame_end - bpy.context.scene.frame_start + 1)]

            #check if 'basis' morph exists
            basis_block = obj.data.shape_keys.key_blocks['basis']
            block = obj.data.shape_keys.key_blocks[str(frame)]
            if block.value != 1.0:
                print(f'{obj.name} incorrect morph value')
            
            for i in range(len(block.data)):
                anm.morphations[frame].append(subVector(block.data[i].co, basis_block.data[i].co))

        anm_list.append(anm)
    return CAnimations(anm_list)



def create_hierarchy(links : dict[str, str]):
    '''
    sets parent for objects in lnks
    '''
    for key, value in links.items():
        if value is None:
            continue
        
        if key in bpy.data.objects and value in bpy.data.objects:
            bpy.data.objects[key].parent = bpy.data.objects[value]
        else:
            print(str(key) + ': object not found in scene, but found in links of hierarchy')

def is_model_correct(model_name):
    obj_count = CItemGroupContainer().get_item_group(model_name).morph_component_count
    print(obj_count)
    collections = bpy.context.scene.collection.children
    if len(collections) < 0:
        print('scene empty')
        return False

    for coll_name in model().morph_collection:
        if bpy.data.collections.get(coll_name) is None:
            print('no "%s" collection found ' % coll_name)
    bEtherlord = bpy.context.scene.ether

    root_list = []

    base_coll = get_collection()
    #check if root object only 1
    for obj in base_coll.objects:
        if obj.type != 'MESH':
            continue
        
        if obj.parent is None:
            root_list.append(obj.name)

        mesh : bpy.types.Mesh = obj.data
        if mesh.uv_layers.active_index < 0:
            print('mesh ' + mesh.name + ' has no active uv layer (UV map)')
            return False


        for i in range(obj_count):
            morph_coll = bpy.data.collections.get(model().morph_collection[i])
            if (model().morph_comp[i] + obj.name) not in morph_coll.objects:
                print('cannot find object: ' + model().morph_comp[i] + obj.name)
                return False

    if len(root_list) != 1:
        print('incorrect root objects, must be only one, exist: ' + str(root_list))

    #check assembly name
    for obj in base_coll.objects:
        if obj.name == model().name:
            print(f'object {obj.name} must not be the same as model name. input another name for model or object')
            return False

    return True

def parts_ordered(links : dict[str, str], links_out : dict[str, str], root):
    '''
    converts hierarchy to ordered list
    '''
    candidates=dict()
    if links[root] is None:
        links_out[root] = None

    for child, parent in links.items():
        if parent is None:
            continue

        if parent == root:
            candidates[child] = parent

    #alphabetical dict sort
    od = py_collections.OrderedDict(sorted(candidates.items()))
    #len(key) dict sort
    new_d = {}
    for k in sorted(od, key=len):
        new_d[k] = od[k]

    for child, parent in new_d.items():
        links_out[child] = parent
        parts_ordered(links, links_out, child)
    

def collect_links(collection_name="base"):
    lnk = CLink()
    base_coll = get_collection(collection_name)

    for obj in base_coll.objects:
        if obj.type != 'MESH':
            continue
        print(obj.name)
        lnk.add(obj.name, obj.parent.name if obj.parent is not None else None)

    lnk_ordered : dict[str, str] = dict()
    parts_ordered(lnk.links, lnk_ordered, lnk.root)
    lnk.links = lnk_ordered
    return lnk

def collect_pos(model_name, include_meshes=None):
    err = 0
    obj_count = CItemGroupContainer().get_item_group(model_name).morph_component_count
    base_coll = get_collection()
    #model().pos_list.clear()
    for obj in base_coll.objects:
        if obj.type != 'MESH':
            continue
        if include_meshes and obj.name not in include_meshes:
            continue
        bone = CBone()
        for i in range(obj_count):
            morph_coll = bpy.data.collections.get(model().morph_collection[i])
            #TODO: if object has no this morph comp, use previous components (end-point: base)
            morph_obj = morph_coll.objects[model().morph_comp[i] + obj.name]
            bone.pos.append(morph_obj.location[:])
            #print(str(obj.name) + '.bonename, objcount' + str(obj_count) + ' loc ' + str(morph_obj.location[:]))
       
        bone.name = obj.name

        if obj_count == 1:
            bone.fillPositions()

        model().pos_list.append(bone)
    return err

def collect_mesh(include_meshes=None):
    err = 0
    item = CItemGroupContainer().get_item_group(model().name)
    obj_count = item.morph_component_count
    base_coll = get_collection()

    individual_group=['helms', 'second layer', 'arrows', 'shield', 'exshield', 'archery', 'archery2', 'weapons left', 'weapons', 'armr', 'staffleft', 'stafflefttwo', 'staffright', 'staffrighttwo']

    for obj in base_coll.objects:
        if obj.type != 'MESH':
            continue
        if include_meshes and obj.name not in include_meshes:
            continue
        figure = CFigure()
        obj_group = CItemGroupContainer().get_item_group(obj.name)
        if obj_group.type in individual_group:
            figure.header[7] = obj_group.ei_group
            figure.header[8] = obj_group.t_number
        else:
            figure.header[7] = item.ei_group
            figure.header[8] = item.t_number
        for i in range(obj_count):
            #TODO: if object has no this morph comp, use previous components (end-point: base)
            morph_coll = bpy.data.collections.get(model().morph_collection[i])
            morph_mesh : bpy.types.Mesh = morph_coll.objects[model().morph_comp[i] + obj.name].data

            count_vert = 0
            count_norm = 0
            v_restore = 0
            ind_count = 0
            duplicate_vert = 0
            duplicate_ind = [[], []]
            min_m = [0, 0, 0]
            max_m = [0, 0, 0]

            # VERTICES & NORMALS
            for mvert in morph_mesh.vertices:
                same_flag = False
                #collect duplicate vertices
                for same_vert in range(count_vert):
                    if mvert.co == figure.verts[i][same_vert]:
                        same_flag = True
                        if i == 0:
                            duplicate_ind[0].append(same_vert)
                            duplicate_ind[1].append(duplicate_vert)
                if not same_flag:
                    # vertices
                    figure.verts[i].append(tuple(mvert.co))
                    count_vert += 1
                    # normals
                    if i == 0:
                        figure.normals.append(tuple([mvert.normal[0], mvert.normal[1],
                                mvert.normal[2], 1.0]))
                        count_norm += 1
                    # MIN & MAX PREPARE
                    if mvert.index == 0:
                        min_m = copy.copy(mvert.co)
                        max_m = copy.copy(mvert.co)
                    for xyz in range(3):
                        if max_m[xyz] < mvert.co[xyz]: max_m[xyz] = mvert.co[xyz]
                        if min_m[xyz] > mvert.co[xyz]: min_m[xyz] = mvert.co[xyz]
                if i == 0:
                    duplicate_vert += 1
 
            figure.fmin.append(tuple(min_m))
            figure.fmax.append(tuple(max_m))
            # RADIUS
            figure.radius.append(sqrt(
                (max_m[0] - min_m[0]) ** 2 +\
                    (max_m[1] - min_m[1]) ** 2 +\
                    (max_m[2] - min_m[2]) ** 2) / 2)
            # CENTER
            figure.center.append(mulVector(sumVector(min_m, max_m), 0.5))
            if count_vert != 0 and i == 0:
                figure.header[5] = count_vert
                figure.generate_m_c()
            
            #move min/max to center of model for world objects
            if obj_group.type == 'world objects':
                figure.fmin[-1] = tuple(subVector(figure.fmin[-1], figure.center[-1]))
                figure.fmax[-1] = tuple(subVector(figure.fmax[-1], figure.center[-1]))

            # align vertices
            v_restore = (4 - (count_vert % 4)) % 4 # fill count until %4 will be 0
            for _ in range(v_restore):
                figure.verts[i].append((0.0, 0.0, 0.0))
                count_vert += 1
            
            if i == 0: # ONLY FOR BASE OBJECT
                figure.header[0] = int(count_vert / 4)
                if len(figure.normals) % 4 != 0:
                    for _ in range(4 - len(figure.normals) % 4):
                        figure.normals.append(
                            copy.copy(figure.normals[count_norm - 1]))
                        count_norm += 1
                figure.header[1] = int(len(figure.normals) / 4)
                ind_ar = []
                for mpoly in morph_mesh.polygons:
                    # INDICES PREPARE
                    for poly_vrt in mpoly.vertices:
                        same_flag = False
                        # remove duplicate indices
                        for dp_vrt in range(len(duplicate_ind[1])):
                            if poly_vrt == duplicate_ind[1][dp_vrt]:
                                same_flag = True
                                ind_ar.append(duplicate_ind[0][dp_vrt])
                        if not same_flag:
                            ind_ar.append(poly_vrt)
                        ind_count += 1
                # UV COORDS PREPARE
                uv_ar = []  # array with all t_coords
                new_uv_ind = []
                # get only active layer with uv_cords
                for uv_act in morph_mesh.uv_layers.active.data:
                    uv_ = [uv_act.uv[0], uv_act.uv[1]]
                    uv_ar.append(copy.copy(uv_))
                    if uv_ not in figure.t_coords:
                        figure.t_coords.append(uv_)
                # get indicies of new t_coords array
                for uv_ind1 in uv_ar:
                    for uv_ind2 in figure.t_coords:
                        if uv_ind1 == uv_ind2:
                            new_uv_ind.append(figure.t_coords.index(uv_ind2))
                # VERTEX COMPONENTS
                for n_i in range(len(ind_ar)):
                    uv_ind = [ind_ar[n_i], new_uv_ind[n_i]]
                    if uv_ind not in figure.v_c:
                        figure.v_c.append(copy.copy(uv_ind))
                #>>>>>TODO use other sort instead bubble sort
                for _ in range(len(figure.v_c)):
                    for buble in range(len(figure.v_c) - 1):
                        if figure.v_c[buble][0] > figure.v_c[buble + 1][0]:
                            swap_pts = copy.copy(figure.v_c[buble + 1])
                            figure.v_c[buble + 1] = copy.copy(figure.v_c[buble])
                            figure.v_c[buble] = copy.copy(swap_pts)
                        elif figure.v_c[buble][0] == figure.v_c[buble + 1][0]:
                            if figure.v_c[buble][1] > figure.v_c[buble + 1][1]:
                                swap_pts = copy.copy(figure.v_c[buble + 1])
                                figure.v_c[buble + 1] = copy.copy(figure.v_c[buble])
                                figure.v_c[buble] = copy.copy(swap_pts)
                figure.header[4] = len(figure.v_c)
                # INDICIES
                #>>>>>TODO refactore?!
                for mix in range(len(ind_ar)):
                    for mix1 in range(len(figure.v_c)):
                        if (ind_ar[mix] == figure.v_c[mix1][0]) and\
                                (new_uv_ind[mix] == figure.v_c[mix1][1]):
                            figure.indicies.append(mix1)
                            break

                figure.header[2] = len(figure.t_coords)
                figure.header[3] = ind_count
        
        figure.name = obj.name
        if obj_count == 1:
            figure.fillVertices()
            figure.fillAux()
            
            
        model().mesh_list.append(figure)

    return err

def clear_unlinked_data():
    for mesh in bpy.data.meshes:
        if mesh.users == 0:
            bpy.data.meshes.remove(mesh)
    for obj in bpy.data.objects:
        if obj.users == 0:
            bpy.data.objects.remove(obj)
    for col in bpy.data.collections:
        if col.users == 0:
            bpy.data.collections.remove(col)

def scene_clear():
    '''
    deletes objects, meshes and collections from scene
    '''
    for collection in bpy.context.scene.collection.children:
        for obj in collection.objects:
            bpy.data.objects.remove(obj, do_unlink=True)
        bpy.data.collections.remove(collection)
    for rem_mesh in bpy.data.meshes:
        if rem_mesh.users == 0:
            bpy.data.meshes.remove(rem_mesh)
    #the blender does not have a single solution for cleaning the scene. this method was invented to try to clean up the scene in any way =\
    if len(bpy.data.objects) > 0:
        for obj in bpy.data.objects:
            bpy.data.objects.remove(obj)
        scene_clear()
    
    #restore animation data to default
    bpy.context.scene.frame_end = 250
    bpy.context.scene.frame_set(1)

def triangulate(cur_obj):
    mesh = cur_obj.data
    blender_mesh = bmesh.new()
    blender_mesh.from_mesh(mesh)
    bmesh.ops.triangulate(blender_mesh, faces=blender_mesh.faces[:], quad_method='BEAUTY', ngon_method='BEAUTY')
    blender_mesh.to_mesh(mesh)
    blender_mesh.free()

def to_object_mode():
    '''
    sets all meshes to 'OBJECT MODE'
    '''
    scene = bpy.context.scene
    for obj in bpy.data.objects:
        if obj.type == 'MESH':
            bpy.context.view_layer.objects.active = obj
            bpy.ops.object.mode_set(mode='OBJECT', toggle=False)


def add_morph_comp(act_obj, morph_component):
    '''
    copys base object on new layer according to morphing prefix
    '''
    if (morph_component + act_obj.name) not in bpy.data.objects:
        # create copy of object
        new_obj = act_obj.copy()
        new_obj.data = act_obj.data.copy()
        new_obj.name = (morph_component + act_obj.name)
        new_obj.data.name = (morph_component + act_obj.name)
        scene = bpy.context.scene
        scene.objects.link(new_obj)
        for i in bpy.types.Scene.model.morph_comp:
            if bpy.types.Scene.model.morph_comp[i] == morph_component:
                if morph_component not in scene.collection.children:
                    # make new collection for this morph component
                    bpy.data.collections.new(bpy.types.Scene.model.morph_collection[i])
                    scene.collection.children.link(bpy.types.Scene.model.morph_collection[i])
                col = scene.collection.children[bpy.types.Scene.model.morph_collection[i]]
                col.objects.link(new_obj)
    else:
        print(act_obj.name + ' it is a bad object to add morph component, try another object')

def calculate_mesh(self, context):
    '''
    calculates test unit using data (str, dex, height) from scene
    '''
    q_str = context.scene.mesh_str
    q_dex = context.scene.mesh_dex
    q_height = context.scene.mesh_height
    for t_mesh in bpy.types.Scene.model.mesh_list:
        if t_mesh in bpy.data.meshes:
            m_verts = bpy.types.Scene.model.fig_table[t_mesh].verts
            for vert in bpy.data.meshes[t_mesh].vertices:
                for i in range(3):
                    temp1 = m_verts[0][vert.index][i] + \
                        (m_verts[1][vert.index][i] - m_verts[0][vert.index][i]) * q_str
                    temp2 = m_verts[2][vert.index][i] + \
                        (m_verts[3][vert.index][i] - m_verts[2][vert.index][i]) * q_str
                    value1 = temp1 + (temp2 - temp1) * q_dex
                    temp1 = m_verts[4][vert.index][i] + \
                        (m_verts[5][vert.index][i] - m_verts[4][vert.index][i]) * q_str
                    temp2 = m_verts[6][vert.index][i] + \
                        (m_verts[7][vert.index][i] - m_verts[6][vert.index][i]) * q_str
                    value2 = temp1 + (temp2 - temp1) * q_dex
                    final = value1 + (value2 - value1) * q_height
                    vert.co[i] = final
    for t_pos in bpy.types.Scene.model.pos_lost:
        if t_pos in bpy.data.objects:
            m_pos = bpy.types.Scene.model.bon_table[t_pos].pos
            for i in range(3):
                temp1 = m_pos[0][i] + (m_pos[1][i] - m_pos[0][i]) * q_str
                temp2 = m_pos[2][i] + (m_pos[3][i] - m_pos[2][i]) * q_str
                value1 = temp1 + (temp2 - temp1) * q_dex
                temp1 = m_pos[4][i] + (m_pos[5][i] - m_pos[4][i]) * q_str
                temp2 = m_pos[6][i] + (m_pos[7][i] - m_pos[6][i]) * q_str
                value2 = temp1 + (temp2 - temp1) * q_dex
                final = value1 + (value2 - value1) * q_height
                bpy.data.objects[t_pos].location[i] = final

def auto_fix_scene():
    # switch to object mode first
    to_object_mode()

    # clear select
    for obj in bpy.context.selected_objects:
        obj.select_set(False)

    for obj in bpy.data.objects:
        # выделяем все объекты
        obj.select_set(True)
        # применяем модификаторы
        for sel in bpy.context.selected_objects:
            bpy.context.view_layer.objects.active = sel
            for modifier in sel.modifiers:
                #if modifier.type == 'SUBSURF':
                bpy.ops.object.modifier_apply(modifier=modifier.name)

                # apply transformations
                bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
                triangulate(sel)

    # copy empty components
    pass

def get_donor_acceptor(context: bpy.types.Context) -> [bpy.types.Object, bpy.types.Object]:
    active = context.active_object
    if (active is None):
        raise Exception("No object is active")
    acceptor = active
    selected = context.selected_objects
    donors = list(filter(lambda x: x != active, selected))
    if (len(donors) != 1):
        raise Exception("Exactly two objects need to be selected: first donor, then acceptor")
    donor = donors[0]
    return donor, acceptor

def transform(object):
    # doesn't work
    current_matrix = object.matrix_world.copy()
    mesh = object.data
    original_vertices = [v.co.copy() for v in mesh.vertices]

    bpy.ops.object.mode_set(mode='EDIT')

    # Update to the latest vertex positions
    bpy.ops.mesh.select_all(action='SELECT')

    for i, vertex in enumerate(mesh.vertices):
        print(vertex)
        # Transform the vertex position using the matrix
        transformed_position = current_matrix @ Vector(original_vertices[i])
        vertex.co = transformed_position

    # Reset the object’s transformations
    object.matrix_world = Matrix.Identity(4)

def transform2(object):
    # doesn't work either
    current_matrix = object.matrix_world.copy()

    # Decompose to get location, rotation, and scale
    location, rotation, scale = current_matrix.decompose()

    # Create a new transformation matrix with applied rotation and location
    new_matrix = Matrix.Translation(
        location) @ rotation.to_matrix().to_4x4() @ Matrix.Diagonal(scale).to_4x4()

    # Set the object's matrix to the new matrix
    object.matrix_world = new_matrix

    # Reset the local rotation and scale (if necessary)
    object.location = (0, 0, 0)
    object.rotation_euler = (0.0, 0.0, 0.0)
    object.rotation_quaternion = (1.0, 0.0, 0.0, 0.0)
    object.scale = (1.0, 1.0, 1.0)

def animation_to_shapekey(context):
    donor, acceptor = get_donor_acceptor(context)
    armature = donor
    acceptor.shape_key_clear()

    bAutofix = bpy.context.scene.skeletal
    if not bAutofix:
        base_key = acceptor.shape_key_add(name='basis', from_mix=False)
    # huh
    # for i, vertex in enumerate(donor.data.vertices):
    #     base_key.data[i].co = vertex.co
    # for animating verts
    depgraph = context.evaluated_depsgraph_get()
    for frame in range(context.scene.frame_start, context.scene.frame_end + 1):
        context.scene.frame_set(frame)
        if not bAutofix:
            # animate vertices
            donor_bm = bmesh.new()
            donor_bm.from_object(donor, depgraph)
            donor_bm.verts.ensure_lookup_table()
            #donor_verts = donor.data.vertices
            donor_verts = donor_bm.verts

            # copy verts from donor to acceptor
            new_key = acceptor.shape_key_add(name=str(frame), from_mix=False)

            #bpy.ops.object.transform_apply(location=True, rotation=True, scale=False)
            for i, vertex in enumerate(donor_verts):
                new_key.data[i].co = vertex.co
                vertex: bmesh.types.BMVert
                # new_key.data[i].co = donor.matrix_world @ vertex.co
                #new_key.data[i].x = vertex.x + armature.location[0]
                #new_key.data[i].y = vertex.y + armature.location[1]
                #new_key.data[i].z = vertex.z + armature.location[2]
            # print(new_key.data[0].co, donor_verts[0].co)
                
            #bpy.ops.transform.transform(value=(donor.location.x,donor.location.y,donor.location.z, 1))
            insert_keyframe(new_key, frame)
        
        if bAutofix:
            #acceptor.rotation_euler[0] = -armature.rotation_euler[1]-0.385398-0.16
            #acceptor.rotation_euler[0] = -armature.rotation_euler[1]*2-0.385398-0.16

    #        acceptor.rotation_euler[0] = -armature.rotation_euler[1]-0.385398-0.16
    #        acceptor.rotation_euler[1] = armature.rotation_euler[0]
    #        acceptor.rotation_euler[2] = armature.rotation_euler[2]+1.570796
            acceptor.rotation_quaternion[0] = armature.rotation_quaternion[0]
            acceptor.rotation_quaternion[1] = armature.rotation_quaternion[1]
            acceptor.rotation_quaternion[2] = armature.rotation_quaternion[2]
            acceptor.rotation_quaternion[3] = armature.rotation_quaternion[3]

            #acceptor.rotation_euler[2] = armature.rotation_euler[2]-1.570796-1.570796
            acceptor.keyframe_insert(data_path='rotation_quaternion', index=-1)

            #acceptor.location[0] = armature.location[0]/100+0.028571

    #        acceptor.location[0] = armature.location[0]+2.8571/100
    #        acceptor.location[1] = armature.location[1]
    #        acceptor.location[2] = (armature.location[2]/100+ (0.08+8)/100)
            acceptor.location[0] = armature.location[0]
            acceptor.location[1] = armature.location[1]
            acceptor.location[2] = armature.location[2]
            
            acceptor.keyframe_insert(data_path='location', index=-1)
            
            #acceptor.scale = donor.scale*100
            #acceptor.scale = [1,1,1]
            acceptor.scale = donor.scale
            
            #acceptor.transform_apply(location=False, rotation=False, scale=True)
            acceptor.keyframe_insert(data_path='scale', index=-1)

# set cursor
# bpy.context.scene.cursor.location = (0, 0, 0)
# set origin to cursor
# bpy.ops.object.origin_set(type='ORIGIN_CURSOR', center='MEDIAN')
# set location
# obj.location = (0, 0, 0)

# def rebase_animation(obj):
#     if obj is None:
#         raise Exception("Error: null object to bake")
#
#     #bpy.context.view_layer.objects.active = obj
#     #bpy.ops.object.transform_apply(location=True, rotation=True)
#
#     # Bake the current animation
#     bpy.ops.nla.bake(frame_start=bpy.context.scene.frame_start,
#                      frame_end=bpy.context.scene.frame_end,
#                      only_selected=False,
#                      visual_keying=True,
#                      clear_constraints=False,
#                      use_current_action=True)

def select_collection(coll_name, append_selection=False):
    coll = bpy.data.collections.get(coll_name)
    if not append_selection:
        bpy.ops.object.select_all(action='DESELECT')
    for obj in coll.objects:
        obj.select_set(True)

def copy_collection(copy_from_name, copy_to_name, name_prefix=None):
    from_collection = bpy.data.collections.get(copy_from_name)
    # make new collection
    to_collection = bpy.data.collections.new(copy_to_name)
    bpy.context.scene.collection.children.link(to_collection)

    # store old-new object links
    prototypes = {}
    def copy_recursive(copy_from, copy_to, parent=None):
        for obj in copy_from:
            new_obj = obj.copy()
            new_obj.data = obj.data.copy()
            if name_prefix:
                new_obj.name = name_prefix + obj.name
            copy_to.objects.link(new_obj)

            prototypes[new_obj.name] = obj.name

            new_obj.parent = parent

            if obj.children:
                copy_recursive(obj.children, copy_to, parent=new_obj)

    root_objects = get_root_objects(from_collection.objects, True)
    copy_recursive(root_objects, to_collection)
    return to_collection, prototypes

def create_all_morphs(context, include_meshes=None):
    links = dict()
    # Триангулируем и применяем модификаторы на базовой модели
    bAutofix = context.scene.auto_apply
    if bAutofix:
        auto_fix_scene()

    scn = scene = context.scene
    scaled = scn.scaled

    #clear_old_morphs(1, include_meshes)

    base_coll = get_collection("base")
    for obj in base_coll.objects:
        if obj.type != 'MESH':
            continue
        links[obj.name] = obj.parent.name if obj.parent else None

    ensure_morph_collections()

    for obj in base_coll.objects:
        if obj.type != 'MESH':
            continue
        if include_meshes and obj.name not in include_meshes:
            continue
        # добавляем коллекции
        for i in range(1, 8):
            coll_name = model().morph_collection[i]
            coll = scene.collection.children[coll_name]
            morph_name = model().morph_comp[i] + obj.name
            if morph_name in coll.objects:
                bpy.data.objects.remove(coll.objects.get(morph_name))
            # копируем меши
            #detect suitable obj
            new_obj = obj.copy()
            new_obj.name = morph_name
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
            if include_meshes and obj.name not in include_meshes:
                continue
            obj.select_set(True)
            bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
            obj.select_set(False)

def report_info(message, title="Note", icon="INFO"):
    bpy.context.window_manager.popup_menu(lambda self, context: self.layout.label(text=message),
                                          title=title, icon=icon)

def get_root_objects(objects: typing.Sequence[bpy.types.Object], all=False):
    root_objects = []
    for obj in objects:
        if obj.parent is None:
            root_objects.append(obj)
    if all:
        return root_objects
    assert (len(root_objects) == 1)
    return root_objects[0]

def get_collection_frame_range(collection_name):
    coll = get_collection(collection_name)
    obj = get_root_objects(coll.objects)

    if not obj.animation_data or not obj.animation_data.action:
        return None

    action = obj.animation_data.action
    frame_range = []

    for fcurve in action.fcurves:
        for keyframe in fcurve.keyframe_points:
            frame_range.append(keyframe.co[0])

    if frame_range:
        start_frame = min(frame_range)
        end_frame = max(frame_range)
        return int(start_frame), int(end_frame)

    return None

def bake_transform_animation(context):
    # create a copy of object -> acceptor
    # for every animation frame:
    # create additional copy of object, apply-transform it and make it a shapekey for acceptor
    # remove original

    selected = context.selected_objects.copy()
    bpy.ops.object.select_all(action='DESELECT')

    skipped = []
    to_process = []
    for obj in selected:
        if obj.data.shape_keys:
            skipped.append(obj.name)
            print(f"Skipped {obj.name} - already has shapekey animation")
            continue
        to_process.append(obj)
        obj.select_set(True)

    if skipped:
        report_info(f"Skipped {skipped} - already has shapekey animation", icon="QUESTION")

    #collection_name = "base"
    #frame_range = get_collection_frame_range(collection_name)
    # if frame_range is None:
    #     raise Exception(f"No animation detected for {collection_name} root object")
    frame_range = context.scene.frame_start, context.scene.frame_end

    # prepare
    context.scene.frame_set(999)
    pairs = []
    for obj in to_process:
        donor, acceptor = bake_make_acceptor(context, obj)
        pairs.append((donor, acceptor))
    # main run
    frame_start, frame_end = frame_range
    frames = list(range(frame_start, frame_end + 1))
    for frame in frames:
        context.scene.frame_set(frame)
        for donor, acceptor in pairs:
            bake_transform_animation_frame(context, donor, acceptor, frame)
    # remove donor
    for donor, acceptor in pairs:
        acceptor.name = donor.name
        bpy.data.objects.remove(donor, do_unlink=True)

def bake_make_acceptor(context, donor):
    # for coll in bpy.data.collections["body"]:
    acceptor = donor.copy()
    acceptor.data = donor.data.copy()
    acceptor.animation_data_clear()
    acceptor.shape_key_clear()

    for collection in donor.users_collection:
        collection.objects.link(acceptor)

    # apply transforms
    bpy.ops.object.select_all(action='DESELECT')
    acceptor.select_set(True)
    # clear initial transform
    bpy.ops.object.rotation_clear()
    bpy.ops.object.location_clear()
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    acceptor.shape_key_add(name='basis', from_mix=False)
    return donor, acceptor

def bake_transform_animation_frame(context, donor, acceptor, frame):
    frame_donor = donor.copy()
    frame_donor.data = donor.data.copy()
    frame_donor.animation_data_clear()
    context.collection.objects.link(frame_donor)

    # apply transforms on selected objects
    bpy.ops.object.select_all(action='DESELECT')
    frame_donor.select_set(True)
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

    new_key = acceptor.shape_key_add(name=str(frame), from_mix=False)
    donor_verts = frame_donor.data.vertices
    for i, vertex in enumerate(donor_verts):
        vertex: bmesh.types.BMVert
        new_key.data[i].co = vertex.co
    insert_keyframe(new_key, frame)
    bpy.data.objects.remove(frame_donor, do_unlink=True)
