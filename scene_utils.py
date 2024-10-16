# Copyright (c) 2022 konstvest
import importlib
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
from typing import Set, Tuple, List
import numpy as np


from . utils import subVector, sumVector, CItemGroupContainer, CItemGroup, mulVector, sumVector
from . import utils as fig_utils
from . bone import CBone
from . import figure
CFigure = figure.CFigure
from . resfile import ResFile
from . scene_management import CModel, CAnimations
from . animation import CAnimation
from . links import CLink
from . utils import CByteReader

profilehooks = None
try:
    from .dev import profilehooks
except ImportError:
    print("No profilehooks")
    pass

def profile(func):
    if profilehooks is not None:
        return profilehooks.profile(immediate=True)(func)
    else:
        return func

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

    model_links = read_model(res_file, model_name, include_meshes)
    bEtherlord = bpy.context.scene.ether
    if not bEtherlord:
        read_bones(res_file, model_name)
    create_model_meshes(model_links)

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

    create_model_meshes(model_links, include_meshes)


def create_model_meshes(links: CLink, include_meshes=None):
    active_model: CModel = bpy.types.Scene.model

    bpy.context.window_manager.progress_update(15)
    scene_clear()
    bpy.context.window_manager.progress_update(49)
    container = CItemGroupContainer()
    item_group = container.get_item_group(active_model.name)
    ensure_morph_collections()

    len_meshes = len(active_model.mesh_list)
    for i, fig in enumerate(active_model.mesh_list):
        bpy.context.window_manager.progress_update(49 + int(i / len_meshes * 50))
        create_mesh_2(fig, item_group)
    create_links_2(links, item_group.morph_component_count)
    for bone in active_model.pos_list:
        morph_count = container.get_item_group(bone.name).morph_component_count
        set_pos_2(bone, morph_count)

@profile
def import_model(context, res_file, model_name, include_meshes: Set[str]=None):
    if (model_name + '.mod') in res_file.get_filename_list():
        import_mod_file(res_file, model_name, include_meshes)
    elif (model_name + '.lnk') in res_file.get_filename_list():
        import_lnk_fig_bon_files(res_file, model_name)
    else:
        return None
    return True

@profile
def export_model(context, res_path, model_name, include_meshes=None):
    links = collect_links()

    active_model: CModel = bpy.types.Scene.model
    active_model.reset()
    active_model.name = model_name

    collect_pos(model_name, include_meshes)
    ModelExporter.collect_mesh(include_meshes)

    # backup_path = res_path + ".backup"
    # with open(res_path, "wb") as dst:
    #     with open(backup_path, "rb") as src:
    #         dst.write(src.read())

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
        initial_model = None
        initial_bone = None
        if include_meshes:
            with ResFile(res_path, 'r') as res:
                with res.open(active_model.name + '.mod', 'r') as file:
                    initial_model = file.read()
                with res.open(active_model.name + '.bon', 'r') as file:
                    initial_bone = file.read()

        # prepare links + figures (.mod file)
        model_res = io.BytesIO(initial_model)
        open_mode = 'a' if initial_model else 'w'
        with ResFile(model_res, open_mode) as res:
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
        bone_res = io.BytesIO(initial_bone)
        with ResFile(bone_res, open_mode) as res:
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

def tris_mesh_from_pydata(mesh: bpy.types.Mesh, vertices: np.array, triangles: np.array):
    vertices_len = len(vertices)
    tris_len = len(triangles)

    mesh.vertices.add(vertices_len)
    len_loops = 3 * len(triangles)
    mesh.loops.add(len_loops)
    mesh.polygons.add(tris_len)

    mesh.vertices.foreach_set("co", vertices.flatten())
    # skip edges
    loop_starts = np.arange(tris_len) * 3
    loop_totals = np.full(tris_len, 3)

    mesh.polygons.foreach_set("loop_start", loop_starts)
    mesh.polygons.foreach_set("loop_total", loop_totals)
    mesh.polygons.foreach_set("vertices", triangles.flatten())

    # if tris_len:
    #     mesh.update(
    #         calc_edges=bool(tris_len),
    #         # Flag loose edges.
    #         calc_edges_loose=bool(False),
    #     )

# @profile
def create_mesh_2(figure: CFigure, item_group: CItemGroup):
    # create mesh, replacing old in collection or renaming same-named mesh elsewhere
    active_model : CModel = bpy.context.scene.model

    n_components = figure.header[3] - figure.header[3] % 3
    indexes = figure.indicies[:n_components]
    n_tris = n_components // 3
    component_indexes = indexes
    vertex_components = figure.v_c
    indexed_components = vertex_components[component_indexes]
    vertex_indices = indexed_components[:, 0]
    vertex_indices = vertex_indices.reshape((n_tris, 3))

    bEtherlord = bpy.context.scene.ether
    if not bEtherlord:
        mesh_count = item_group.morph_component_count
    else:
        mesh_count = 1

    print('create meshes for', figure.name)

    # mesh_uvs = np.array(figure.t_coords)
    mesh_uvs = figure.t_coords
    uv_indices = indexed_components[:, 1]
    uvs = mesh_uvs[uv_indices]
    assert len(uvs) == figure.header[3]
    uvs_flat = uvs.flatten()

    for i in range(mesh_count):
        collection_name = active_model.morph_collection[i]
        collection = get_collection(collection_name)
        name = active_model.morph_comp[i] + figure.name
        # remove old mesh
        old_obj_collection = collection.objects.get(name)
        if old_obj_collection:
            bpy.data.objects.remove(old_obj_collection)
        old_obj = bpy.data.objects.get(name)
        if old_obj:
            rename_serial(old_obj, name)
        # insert new mesh
        mesh = bpy.data.meshes.new(name=name)
        base_obj = bpy.data.objects.new(name, mesh)
        base_obj.location = (0, 0, 0)
        collection.objects.link(base_obj)
        tris_mesh_from_pydata(mesh, figure.verts[i], vertex_indices)
        # mesh.from_pydata(figure.verts[i], [], vertex_indices)
        mesh.uv_layers.new(name=bpy.context.scene.model.name)
        mesh.uv_layers[0].data.foreach_set('uv', uvs_flat)
        mesh.update()

def set_pos_2(bone : CBone, morph_count):
    active_model : CModel = bpy.context.scene.model
    
    for obj_num in range(morph_count):
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

class ModelExporter:

    @staticmethod
    def calculate_figure_bounds(mesh_group, figure: CFigure, vertices):
        min_m = []
        max_m = []
        for xyz in range(3):
            min_co = min(vertices, key=lambda vert: vert[xyz])
            max_co = max(vertices, key=lambda vert: vert[xyz])
            min_m.append(min_co[xyz])
            max_m.append(max_co[xyz])

        figure.fmin.append(tuple(min_m))
        figure.fmax.append(tuple(max_m))
        # RADIUS
        figure.radius.append(sqrt(
            (max_m[0] - min_m[0]) ** 2 + \
            (max_m[1] - min_m[1]) ** 2 + \
            (max_m[2] - min_m[2]) ** 2) / 2)
        # CENTER
        figure.center.append(mulVector(sumVector(min_m, max_m), 0.5))

        # move min/max to center of model for world objects
        if mesh_group.type == 'world objects':
            figure.fmin[-1] = tuple(subVector(figure.fmin[-1], figure.center[-1]))
            figure.fmax[-1] = tuple(subVector(figure.fmax[-1], figure.center[-1]))

    @staticmethod
    def calculate_figure_bounds_np(obj_group, figure: CFigure, vertices):
        min_m = vertices.min(axis=0)
        max_m = vertices.max(axis=0)

        figure.fmin.append(tuple(min_m))
        figure.fmax.append(tuple(max_m))
        # RADIUS
        figure.radius.append((((max_m - min_m) ** 2).sum() ** 1/2) / 2)
        # CENTER
        figure.center.append(mulVector(sumVector(min_m, max_m), 0.5))

        # move min/max to center of model for world objects
        if obj_group.type == 'world objects':
            figure.fmin[-1] = tuple(subVector(figure.fmin[-1], figure.center[-1]))
            figure.fmax[-1] = tuple(subVector(figure.fmax[-1], figure.center[-1]))

    @staticmethod
    def align_length_by_4(vertices, align_element=None):
        # ensure vertex count is divisible by 4
        to_append = (4 - (len(vertices) % 4)) % 4
        for _ in range(to_append):
            vertices.append(align_element)
        return vertices

    @staticmethod
    def align_length_by_4_np(vertices):
        to_append = (4 - (len(vertices) % 4)) % 4
        padded = np.zeros((vertices.shape[0] + to_append, vertices.shape[1]), vertices.dtype)
        padded[: vertices.shape[0], :] = vertices
        return padded

    @staticmethod
    def collect_base_mesh_simple(figure, mesh: bpy.types.Mesh):
        # export base mesh
        figure.t_coords = []
        figure.v_c = []
        uv_data = mesh.uv_layers.active.data

        for loop_index, loop in enumerate(mesh.loops):
            vertex_index = loop.vertex_index
            uv = uv_data[loop_index].uv
            figure.t_coords.append([uv[0], uv[1]])
            uv_index = len(figure.t_coords) - 1
            figure.v_c.append((vertex_index, uv_index))
            vc_index = len(figure.v_c) - 1
            figure.indicies.append(vc_index)

        figure.header[0] = int(len(figure.verts[0]) / 4)
        figure.header[1] = int(len(figure.normals) / 4)
        figure.header[2] = len(figure.t_coords)
        figure.header[3] = len(figure.indicies)
        figure.header[4] = len(figure.v_c)

    @staticmethod
    def collect_base_mesh_simple_np(figure, mesh: bpy.types.Mesh, mesh_group: CItemGroup):
        n_vertex = len(mesh.loops)

        vertex_components = np.zeros((n_vertex, 2), dtype=np.int)
        vertex_indices = np.zeros(n_vertex, dtype=np.int)
        mesh.loops.foreach_get('vertex_index', vertex_indices)
        vertex_components[:, 0] = vertex_indices
        vertex_components[:, 1] = np.arange(n_vertex)
        figure.v_c = vertex_components
        # uvs
        uv_data = mesh.uv_layers.active.data
        uvs = np.zeros(n_vertex * 2, np.float32)
        uv_data.foreach_get('uv', uvs)
        uvs.shape = (n_vertex, 2)

        packed_uvs = fig_utils.pack_uv_np(uvs, mesh_group.uv_convert_count, mesh_group.uv_base)
        figure.t_coords = packed_uvs
        figure.indicies = np.arange(n_vertex)

        figure.header[0] = int(len(figure.verts[0]) / 4)
        figure.header[1] = int(len(figure.normals) / 4)
        figure.header[2] = len(figure.t_coords)
        figure.header[3] = len(figure.indicies)
        figure.header[4] = len(figure.v_c)

    @staticmethod
    # @profile
    def collect_mesh(include_meshes=None):
        # include_meshes = {"hd.armor28"}
        model().mesh_list = []
        model_group = CItemGroupContainer().get_item_group(model().name)
        obj_count = model_group.morph_component_count
        base_coll = get_collection()

        individual_group = ['helms', 'second layer', 'arrows', 'shield', 'exshield', 'archery', 'archery2', 'weapons left',
                            'weapons', 'armr', 'staffleft', 'stafflefttwo', 'staffright', 'staffrighttwo']

        len_objects = len(base_coll.objects)
        for n_obj, obj in enumerate(base_coll.objects):
            if obj.type != 'MESH':
                continue
            if include_meshes and obj.name not in include_meshes:
                continue
            figure = CFigure()
            mesh_group = CItemGroupContainer().get_item_group(obj.name)
            export_group = mesh_group if mesh_group.type in individual_group else model_group

            figure.header[7] = export_group.ei_group
            figure.header[8] = export_group.t_number
            bpy.context.window_manager.progress_update(n_obj/len_objects * 99)

            for i in range(obj_count):
                # TODO: if object has no this morph comp, use previous components (end-point: base)
                morph_coll = bpy.data.collections.get(model().morph_collection[i])
                morph_mesh: bpy.types.Mesh = morph_coll.objects[model().morph_comp[i] + obj.name].data
                n_vertex = len(morph_mesh.vertices)
                vertices = np.zeros(n_vertex * 3, np.float32)
                morph_mesh.vertices.foreach_get('co', vertices)
                vertices.shape = (n_vertex, 3)
                morph_components = len(morph_mesh.vertices)
                ModelExporter.calculate_figure_bounds_np(mesh_group, figure, vertices)
                padded_vertices = ModelExporter.align_length_by_4_np(vertices)
                figure.verts[i] = padded_vertices
                if i > 0:
                    continue
                normals = np.zeros(n_vertex * 3, np.float32)
                morph_mesh.vertices.foreach_get('normal', normals)
                normals.shape = (n_vertex, 3)
                to_pad = (4 - (n_vertex % 4)) % 4
                normals4 = np.zeros((n_vertex + to_pad, 4), np.float32)
                normals4[:n_vertex, :-1] = normals
                # (x, y, z, 1.0)
                normals4[:, -1] = 1.0
                figure.normals = normals4
                figure.header[5] = morph_components
                figure.generate_m_c()
                ModelExporter.collect_base_mesh_simple_np(figure, morph_mesh, mesh_group)

            figure.name = obj.name
            if obj_count == 1:
                figure.fillVertices()
                figure.fillAux()

            model().mesh_list.append(figure)

        return True

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

    # scene = bpy.context.scene
    # bpy.data.scenes.new("Scene")
    # bpy.data.scenes.remove(scene, do_unlink=True)
    # scene.name = "Scene"
    # return

    # for collection in bpy.context.scene.collection.children:
    #     collection.hide_viewport = False
    #     for obj in collection.objects:
    #         obj.hide_set(False)
    #         obj.select_set(True)
    # bpy.ops.object.delete()

    # prev_ui = bpy.context.area.ui_type
    # area_type = 'OUTLINER'
    # bpy.context.area.ui_type = area_type
    # bpy.ops.outliner.delete(hierarchy=False)
    # bpy.context.area.ui_type = prev_ui
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
