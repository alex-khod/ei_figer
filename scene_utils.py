# Copyright (c) 2022 konstvest
import collections as py_collections
import copy as cp
import importlib
import io
import typing
from typing import Set, Tuple

import bmesh
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
import bpy
import numpy as np
from mathutils import Quaternion, Vector, Matrix, Euler

from . import figure
from . import resfile
from . import utils as fig_utils
from .bone import CBone
from .utils import subVector, CItemGroupContainer, CItemGroup, mulVector, sumVector

# This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.

CFigure = figure.CFigure
from .resfile import ResFile
from .scene_management import CModel, CAnimations
from .animation import CAnimation
from .links import CLink

profilehooks = None
try:
    from .dev import profilehooks
except ImportError:
    print("No profilehooks")
    pass


class TemporaryContext:

    def __init__(self, temp_ui):
        self.temp_ui = temp_ui
        self.prev_ui = None

    def __enter__(self):
        self.prev_ui = bpy.context.area.ui_type
        bpy.context.area.ui_type = self.temp_ui

    def __exit__(self, exc_type, exc_value, tb):
        if exc_type is not None:
            import traceback
            traceback.print_exception(exc_type, exc_value, tb)
        bpy.context.area.ui_type = self.prev_ui


def profile(func):
    if profilehooks is not None:
        return profilehooks.profile(immediate=True)(func)
    else:
        return func


def MODEL() -> CModel:
    return bpy.context.scene.model


def get_collection(collection_name="base") -> bpy.types.Collection:
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
        split = obj.name.rsplit('.', 1)
        if len(split) == 1:
            continue

        name, postfix = split
        digits = '0123456789'

        all_in_digits = [c in digits for c in postfix]
        all_digits = sum(all_in_digits) == len(postfix)
        if not all_digits:
            continue

        if name in bpy.data.objects:
            rename_serial(bpy.data.objects.get(name), name)
        obj.name = name


def read_links(lnk_res: ResFile, lnk_name: str):
    with lnk_res.open(lnk_name) as lnk_res:
        data = lnk_res.read()
        lnk = CLink()
        lnk.read_lnk(data)
    return lnk


def read_figure(fig_res: ResFile, fig_name: str):
    active_model: CModel = bpy.types.Scene.model
    err = 0
    with fig_res.open(fig_name) as fig_res:
        data = fig_res.read()
        fig = CFigure()
        err += fig.read_fig(fig_name, data)
        active_model.mesh_list.append(fig)
        # bon = CBone()
        # err += bon.read_bonvec(fig_name, [1,1,1])
        # active_model.pos_list.append(bon)
        # bpy.context.scene.cursor.location = (1,1,1)
        # bpy.context.scene.tool_settings.transform_pivot_point
    return err


def read_bone(bon_res: ResFile, bon_name: str):
    active_model: CModel = bpy.types.Scene.model
    err = 0
    with bon_res.open(bon_name) as bon_res:
        data = bon_res.read()
        bon = CBone()
        err += bon.read_bon(bon_name, data)
        active_model.pos_list.append(bon)
    return err


def read_model(res_file: ResFile, model_name, include_meshes=None):
    with res_file.open(model_name + '.mod') as meshes_container:
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


def read_bones(res_file: ResFile, model_name):
    err = 0
    # bones container
    with res_file.open(model_name + '.bon') as bone_container:
        bone_list_res = ResFile(bone_container)
        for bone_name in bone_list_res.get_filename_list():
            err += read_bone(bone_list_res, bone_name)
    return err


def read_animations(res_file: ResFile, model_name: str, animation_name: str) -> CAnimations:
    anm_list = []
    with res_file.open(model_name + '.anm') as animation_container:
        anm_res_file = ResFile(animation_container)
        with anm_res_file.open(animation_name) as animation_file:
            animation_res = ResFile(animation_file)
            for part_name in animation_res.get_filename_list():  # set of parts
                with animation_res.open(part_name) as part_res:
                    part = part_res.read()
                    anm = CAnimation()
                    anm.read_anm(part_name, part)
                    # try:
                    #     anm.read_anm(part_name, part)
                    # except Exception as e:
                    #     print('crash', e)
                    #     continue
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
    print("reading lnk-fig-bon")
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
        if include_meshes and part not in include_meshes:
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
    if not include_meshes:
        clear_morph_collections(start_index=0)
    bpy.context.window_manager.progress_update(30)
    container = CItemGroupContainer()
    item_group = container.get_item_group(active_model.name)
    ensure_morph_collections()

    len_meshes = len(active_model.mesh_list)
    for i, fig in enumerate(active_model.mesh_list):
        bpy.context.window_manager.progress_update(30 + (i / len_meshes * 50))
        create_mesh_2(fig, item_group)
    create_links_2(links, item_group.morph_component_count)
    for bone in active_model.pos_list:
        morph_count = container.get_item_group(bone.name).morph_component_count
        set_pos_2(bone, morph_count)


def import_model(context, res_file, model_name, include_meshes: Set[str] = None):
    if (model_name + '.mod') in res_file.get_filename_list():
        import_mod_file(res_file, model_name, include_meshes)
    elif (model_name + '.lnk') in res_file.get_filename_list():
        import_lnk_fig_bon_files(res_file, model_name)
    else:
        return None
    return True


def get_morph_collections(start_index=1):
    collections = [get_collection(collection_name) for collection_name in CModel.morph_names[start_index:]]
    return collections


def get_base_members_without_morphs():
    without_morphs = py_collections.defaultdict(list)
    for base_obj in get_collection("base").objects:
        for collection, prefix in zip(get_morph_collections(1), CModel.morph_prefixes[1:]):
            morph_member_name = prefix + base_obj.name
            if morph_member_name not in collection.objects:
                without_morphs[base_obj.name].append(morph_member_name)
    return without_morphs


def export_model(context, res_path, model_name, include_meshes=None):
    links = collect_links()

    active_model: CModel = bpy.types.Scene.model
    active_model.reset()
    active_model.name = model_name

    def filter_export(include_meshes=None, exclude_meshes=None):
        def filter_(obj):
            if obj.type != "MESH":
                return False
            if include_meshes and obj.name not in include_meshes:
                return False
            if exclude_meshes and obj.name in exclude_meshes:
                return False
            return True

        return filter_

    base_collection = get_collection("base")
    without_morphs = get_base_members_without_morphs()
    bases_without_morphs = set(without_morphs.keys())
    filter_ = filter_export(include_meshes, exclude_meshes=bases_without_morphs)
    export_objects = list(filter(filter_, base_collection.objects))

    collect_pos(export_objects, model_name)
    is_export_unique = context.scene.is_export_unique
    ModelExporter.collect_mesh(export_objects, is_export_unique)

    # backup_path = res_path + ".backup"
    # with open(res_path, "wb") as dst:
    #     with open(backup_path, "rb") as src:
    #         dst.write(src.read())

    obj_count = CItemGroupContainer().get_item_group(MODEL().name).morph_component_count
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
    return without_morphs


def ei2abs_rotations(links: CLink, animations: CAnimations):
    """
    Calculates absolute rotations for parts in links, based on EI values
    """
    lnk = links.links
    # TODO: check if links correctly (None parent has only 1 obj and other)
    if not links:
        raise Exception("Error: empty links")

    def calc_frames(part: CAnimation):
        if lnk[part.name] is None:  # root object
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

    def calc_frames(part: CAnimation):
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

    def calc_frames(part: CAnimation):
        if lnk[part.name] is None:
            return

        for i in range(len(part.rotations)):
            parent_rot = cp.deepcopy(animations.get_animation(lnk[part.name]).abs_rotation[i])
            parent_rot_invert = parent_rot.inverted().copy()
            child_rot: Quaternion = parent_rot.copy()
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
    # TODO: check if links correctly (None parent has only 1 obj and other)
    if not links:
        raise Exception("Error: empty links")

    def calc_frames(part: CAnimation):
        if lnk[part.name] is None:  # root object
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


def create_mesh_2(figure: CFigure, item_group: CItemGroup):
    # create mesh, replacing old in collection or renaming same-named mesh elsewhere
    active_model: CModel = bpy.context.scene.model

    n_indices = figure.header[3] - figure.header[3] % 3

    print('head', figure.header)
    print('head', figure.header[3])

    indexes = figure.indicies[:n_indices]
    n_tris = n_indices // 3
    component_indexes = indexes
    vertex_components = figure.v_c
    indexed_components = vertex_components[component_indexes]
    vertex_indices = indexed_components[:, 0]
    vertex_indices = vertex_indices.reshape((n_tris, 3))

    is_etherlord = bpy.context.scene.ether
    mesh_count = figure.get_morph_count(figure.signature, is_etherlord)

    print('create (n=%d) meshes for %s' % (mesh_count, figure.name))

    # mesh_uvs = np.array(figure.t_coords)
    mesh_uvs = figure.t_coords
    uv_indices = indexed_components[:, 2]
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


def set_pos_2(bone: CBone, morph_count):
    active_model: CModel = bpy.context.scene.model

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
    model: CModel = bpy.types.Scene.model

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
    sk.keyframe_insert("value", frame=f - 1)
    sk.keyframe_insert("value", frame=f + 1)
    sk.value = 1.0
    sk.keyframe_insert("value", frame=f)


def insert_animation(to_collection: str, anm_list: CAnimations):
    clear_animation_data(to_collection)

    for anim in anm_list:
        if anim.name not in bpy.data.objects:
            print('object ' + anim.name + ' not found in animation list')
            continue

        obj = bpy.data.objects[anim.name]
        obj.rotation_mode = 'QUATERNION'
        bpy.context.scene.frame_end = 0
        bpy.context.scene.frame_end = len(anim.rotations) - 1  # for example, 43 frames from 0 to 42

        # print('rotations', len(part.translations), 'translations', len(part.rotations))

        for frame in range(len(anim.rotations)):
            # rotations
            # bpy.context.scene.frame_set(frame)  # choose frame
            obj.rotation_quaternion = anim.rotations[frame]
            obj.keyframe_insert(data_path='rotation_quaternion', frame=frame, index=-1)

        bEtherlord = bpy.context.scene.ether
        if bEtherlord or obj.parent is None:
            for frame in range(len(anim.translations)):
                obj.location = anim.translations[frame]
                obj.keyframe_insert(data_path='location', frame=frame, index=-1)

        # morphations
        if len(anim.morphations) > 0:
            n_vertices = len(obj.data.vertices)
            vertices_data = np.zeros(n_vertices * 3, np.float32)
            obj.data.vertices.foreach_get('co', vertices_data)
            vertices_data = vertices_data.reshape((n_vertices, 3))

            frame_data = vertices_data.copy()

            obj.shape_key_add(name='basis', from_mix=False)
            for frame in range(len(anim.morphations)):
                key = obj.shape_key_add(name=str(frame), from_mix=False)

                n_animated_vertices = anim.num_morph_verts
                frame_data[:n_animated_vertices] = vertices_data[:n_animated_vertices] + anim.morphations[frame]

                key.data.foreach_set('co', frame_data.flatten())
                insert_keyframe(key, frame)
    return True


def get_res_file_buffer(index):
    return getattr(bpy.context.scene, 'res_file_buffer%d' % index)


def set_res_file_buffer(index, value):
    setattr(bpy.context.scene, 'res_file_buffer%d' % index, value)


def collect_animations(frame_range: Tuple[int, int], collection_name="base"):
    anm_list = []
    coll = get_collection(collection_name)

    # base_collection = get_collection('base')
    # base_obj = base_collection.objects[0]
    # base_data_2 = np.zeros(n_block_data * 3, dtype=np.float32)
    # base_obj.data.vertices.foreach_get('co', base_data_2)
    # base_data_2 = base_data_2.reshape((n_block_data, 3))
    # base_data_2 = np.unique(base_data_2, axis=0)
    # print(base_data_2 == basis_data)
    # breakpoint()

    # base_collection = get_collection("base")
    # obj.data.vertices.foreach_get('co', base_data)

    for obj in coll.objects:
        if obj.name[0:2] in bpy.types.Scene.model.morph_comp.values():
            continue  # skip morphed objects

        if obj.animation_data is None and (not obj.data.shape_keys):
            continue

        # base_obj = base_collection.get(obj.name)
        # base_obj = base_collection.objects[0]
        # n_vertices = len(base_obj.data.vertices)
        # base_verts = np.zeros(n_vertices * 3, np.float32)
        # base_obj.data.vertices.foreach_get('co', base_verts)
        # base_verts = base_verts.reshape((n_vertices, 3))

        anm = CAnimation()
        anm.name = obj.name
        obj.rotation_mode = 'QUATERNION'
        frame_start, frame_end = frame_range

        basis_block = None
        unique_verts_idx = None
        for frame in range(frame_start, frame_end + 1):
            # rotations
            bpy.context.scene.frame_set(frame)  # choose frame
            anm.rotations.append(Quaternion(obj.rotation_quaternion))
            # positions
            bEtherlord = bpy.context.scene.ether
            if not bEtherlord:
                print('object ' + anm.name + ' loc is ' + str(obj.location))
                if obj.parent is None:  # root
                    anm.translations.append(obj.location.copy())
            else:
                anm.translations.append(obj.location.copy())

            # morphations
            if not obj.data.shape_keys:
                continue

            if basis_block is None:
                basis_block = obj.data.shape_keys.key_blocks['basis']
                n_morph_frame_vertices = len(basis_block.data)
                basis_data = np.zeros(n_morph_frame_vertices * 3, np.float32)
                basis_block.data.foreach_get('co', basis_data)
                basis_data = basis_data.reshape((n_morph_frame_vertices, 3))

            block = obj.data.shape_keys.key_blocks[str(frame)]
            if block.value != 1.0:
                print(f'{obj.name} incorrect morph value')

            n_block_data = len(block.data)
            frame_data = np.zeros(n_block_data * 3, dtype=np.float32)
            block.data.foreach_get('co', frame_data)
            frame_data = frame_data.reshape((n_morph_frame_vertices, 3))
            if unique_verts_idx is not None:
                frame_data = frame_data[unique_verts_idx]
            frame_data = frame_data - basis_data
            # frame_data = np.zeros((n_morph_frame_vertices, 3), np.float32)
            anm.morphations.append(frame_data)

        anm_list.append(anm)
    return CAnimations(anm_list)


def create_hierarchy(links: dict[str, str]):
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


def check_morph_items(base_collection, morph_collection: bpy.types.Collection, morph_prefix):
    bad_objects = []
    for base_obj in base_collection.objects:
        base_obj: bpy.types.Object
        name = morph_prefix + base_obj.name
        obj = morph_collection.objects.get(name)
        if not obj:
            print(f"Missing morph object {name}")
            bad_objects.append(name)
            continue
        if len(base_obj.data.vertices) != len(obj.data.vertices):
            print(f"Uneqal mesh length for mesh {name}")
            bad_objects.append(name)
    return bad_objects


def is_model_correct(model_name):
    obj_count = CItemGroupContainer().get_item_group(model_name).morph_component_count
    print(obj_count)
    collections = bpy.context.scene.collection.children
    if len(collections) < 0:
        print('scene empty')
        return False

    missing_morphs = []
    for coll_name in MODEL().morph_collection:
        if bpy.data.collections.get(coll_name) is None:
            missing_morphs.append(coll_name)

    if missing_morphs:
        morph_list = ','.join(missing_morphs)
        print('No "%s" morph collection found. \nProbably should create morphs using `Create all morphs`' % morph_list)
        return False

    base_collection = get_collection("base")
    bad_objects = []
    for morph_name, prefix in zip(MODEL().morph_collection[1:], MODEL().morph_prefixes[1:]):
        morph_collection = get_collection(morph_name)
        bad_objects.extend(check_morph_items(base_collection, morph_collection, prefix))

    if bad_objects and not bpy.context.scene.is_ignore_without_morphs:
        return False

    bEtherlord = bpy.context.scene.ether

    root_list = []
    base_coll = get_collection()
    # check if root object only 1
    for obj in base_coll.objects:
        if obj.type != 'MESH':
            continue

        if obj.parent is None:
            root_list.append(obj.name)

        mesh: bpy.types.Mesh = obj.data
        if mesh.uv_layers.active_index < 0:
            print('mesh ' + mesh.name + ' has no active uv layer (UV map)')
            return False

        # for i in range(obj_count):
        #     morph_coll = bpy.data.collections.get(MODEL().morph_collection[i])
        #     if (MODEL().morph_comp[i] + obj.name) not in morph_coll.objects:
        #         print('cannot find object: ' + MODEL().morph_comp[i] + obj.name)
        #         return False

    if len(root_list) != 1:
        print('incorrect root objects, must be only one, exist: ' + str(root_list))

    # check assembly name
    for obj in base_coll.objects:
        if obj.name == MODEL().name:
            print(f'object {obj.name} must not be the same as model name. input another name for model or object')
            return False

    return True


def parts_ordered(links: dict[str, str], links_out: dict[str, str], root):
    '''
    converts hierarchy to ordered list
    '''
    candidates = dict()
    if links[root] is None:
        links_out[root] = None

    for child, parent in links.items():
        if parent is None:
            continue

        if parent == root:
            candidates[child] = parent

    # alphabetical dict sort
    od = py_collections.OrderedDict(sorted(candidates.items()))
    # len(key) dict sort
    new_d = {}
    for k in sorted(od, key=len):
        new_d[k] = od[k]

    for child, parent in new_d.items():
        links_out[child] = parent
        parts_ordered(links, links_out, child)


def collect_links(collection_name="base"):
    lnk = CLink()
    collection = get_collection(collection_name)

    for obj in collection.objects:
        if obj.type != 'MESH':
            continue
        lnk.add(obj.name, obj.parent.name if obj.parent is not None else None)

    lnk_ordered: dict[str, str] = dict()
    parts_ordered(lnk.links, lnk_ordered, lnk.root)
    lnk.links = lnk_ordered
    return lnk


def collect_pos(objects, model_name):
    err = 0
    obj_count = CItemGroupContainer().get_item_group(model_name).morph_component_count
    for obj in objects:
        bone = CBone()
        for i in range(obj_count):
            morph_coll = bpy.data.collections.get(MODEL().morph_collection[i])
            # TODO: if object has no this morph comp, use previous components (end-point: base)
            morph_obj = morph_coll.objects[MODEL().morph_comp[i] + obj.name]
            bone.pos.append(morph_obj.location[:])
            # print(str(obj.name) + '.bonename, objcount' + str(obj_count) + ' loc ' + str(morph_obj.location[:]))

        bone.name = obj.name

        if obj_count == 1:
            bone.fillPositions()

        MODEL().pos_list.append(bone)
    return err


class ModelExporter:

    @staticmethod
    def calculate_figure_bounds_np(figure: CFigure, vertices, obj_group):
        min_m = vertices.min(axis=0)
        max_m = vertices.max(axis=0)

        figure.fmin.append(tuple(min_m))
        figure.fmax.append(tuple(max_m))
        # RADIUS
        figure.radius.append((((max_m - min_m) ** 2).sum() ** 1 / 2) / 2)
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
    def collect_mesh(objects, collect_unique=False):
        # collect object meshes into CFigure
        MODEL().mesh_list = []
        model_group = CItemGroupContainer().get_item_group(MODEL().name)
        morph_count = model_group.morph_component_count
        len_objects = len(objects)
        for n_obj, obj in enumerate(objects):
            figure = CFigure()
            mesh_group = CItemGroupContainer().get_item_group(obj.name)
            export_group = mesh_group if CItemGroupContainer.is_individual_group(mesh_group.type) else model_group

            figure.header[7] = export_group.ei_group
            figure.header[8] = export_group.t_number
            bpy.context.window_manager.progress_update(n_obj / len_objects * 99)
            for i in range(morph_count):
                # TODO: if object has no this morph comp, use previous components (end-point: base)
                morph_coll = bpy.data.collections.get(MODEL().morph_collection[i])
                morph_mesh: bpy.types.Mesh = morph_coll.objects[MODEL().morph_comp[i] + obj.name].data
                n_vertex = len(morph_mesh.vertices)
                vertices = np.zeros(n_vertex * 3, np.float32)
                morph_mesh.vertices.foreach_get('co', vertices)
                vertices.shape = (n_vertex, 3)
                morph_components = len(vertices)
                ModelExporter.calculate_figure_bounds_np(figure, vertices, export_group)
                vertices_aligned_4 = ModelExporter.align_length_by_4_np(vertices)
                figure.verts[i] = vertices_aligned_4
                if i > 0:
                    continue
                # base normals. same order as mesh.vertices
                normals = np.zeros(n_vertex * 3, np.float32)
                morph_mesh.vertices.foreach_get('normal', normals)
                normals.shape = (n_vertex, 3)
                mesh_normals = normals
                # reindexed normals from non-duplicate vertices
                n_normals = len(mesh_normals)
                to_pad = (4 - (n_normals % 4)) % 4
                normals_aligned_4 = np.zeros((n_normals + to_pad, 4), np.float32)
                normals_aligned_4[:n_normals, :-1] = mesh_normals
                # (x, y, z, 1.0)
                normals_aligned_4[:, -1] = 1.0
                figure.normals = normals_aligned_4
                figure.header[5] = morph_components
                figure.generate_m_c()
                ModelExporter.collect_base_mesh_np(figure, morph_mesh, export_group, collect_unique)
            figure.name = obj.name
            if morph_count == 1:
                figure.fill_vertices()
                figure.fill_bounding_volume()

            MODEL().mesh_list.append(figure)
        return True

    @staticmethod
    def collect_base_mesh_np(figure: CFigure, mesh: bpy.types.Mesh, mesh_group: CItemGroup, collect_unique=True):
        n_index = len(mesh.loops)
        vertex_idx = np.zeros(n_index, dtype=np.uint16)
        mesh.loops.foreach_get('vertex_index', vertex_idx)
        # uvs
        uv_data = mesh.uv_layers.active.data
        uvs = np.zeros(n_index * 2, np.float32)
        uv_data.foreach_get('uv', uvs)
        uvs.shape = (n_index, 2)

        if collect_unique:
            unique_uvs, inverse_uv_idx = np.unique(uvs, axis=0, return_inverse=True)
            uvs = unique_uvs
            uv_idx = inverse_uv_idx
        else:
            uv_idx = np.arange(n_index)

        packed_uvs = fig_utils.pack_uv_np(uvs, mesh_group.uv_convert_count, mesh_group.uv_base)

        figure.t_coords = packed_uvs
        vertex_components = np.zeros((n_index, 3), dtype=np.uint16)
        # geom/vertex index, normal index, uv index
        vertex_components[:, 0] = vertex_idx
        normal_idx = vertex_idx
        vertex_components[:, 1] = normal_idx
        vertex_components[:, 2] = uv_idx

        vertex_components, inverse_vc_idx = np.unique(vertex_components, axis=0, return_inverse=True)
        figure.v_c = vertex_components.astype(np.uint16)
        figure.indicies = inverse_vc_idx.astype(np.uint16)
        # figure.indicies = np.arange(n_index, dtype=np.uint16)

        figure.header[0] = int(len(figure.verts[0]) / 4)
        figure.header[1] = int(len(figure.normals) / 4)
        figure.header[2] = len(figure.t_coords)
        figure.header[3] = len(figure.indicies)
        figure.header[4] = len(figure.v_c)


def unhide_collections_recursive(base_collection: bpy.types.LayerCollection = None):
    if base_collection is None:
        view_layer: bpy.types.ViewLayer = bpy.context.view_layer
        base_collection = view_layer.layer_collection

    for collection in base_collection.children:
        collection.hide_viewport = False
        if collection.children:
            unhide_collections_recursive(collection)


def unhide_objects(base_collection=None):
    for collection in bpy.context.scene.collection.children:
        collection: bpy.types.Collection

        for obj in collection.all_objects:
            obj.hide_set(False)
            obj.select_set(True)


def clear_old_morphs(start_index=1, include_meshes=None):
    return NotImplemented
    # for coll_name, coll_prefix in zip(MODEL().morph_collection[start_index:], MODEL().morph_comp.values()[start_index:]):
    #     coll = get_collection(coll_name)
    #     if not coll:
    #         continue
    #     for obj in coll.objects:
    #         if not include_meshes or obj.name in include_meshes:
    #             bpy.data.objects.remove(obj)
    # return True


def clear_collection(collection_name):
    collection = get_collection(collection_name)
    if collection is None:
        return
    bpy.data.collections.remove(collection)
    with TemporaryContext('VIEW_3D'):
        bpy.ops.outliner.orphans_purge(do_recursive=True)


def clear_morph_collections(start_index=1):
    for collection_name in MODEL().morph_collection[start_index:]:
        collection = bpy.data.collections.get(collection_name)
        if collection:
            bpy.data.collections.remove(collection)
    with TemporaryContext('VIEW_3D'):
        bpy.ops.outliner.orphans_purge(do_recursive=True)


def clear_unlinked_data():
    with TemporaryContext("VIEW_3D"):
        bpy.ops.outliner.orphans_purge(do_recursive=True)
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

    for collection in bpy.data.collections:
        bpy.data.collections.remove(collection)
    bpy.ops.outliner.orphans_purge(do_recursive=True)

    for collection in bpy.context.scene.collection.children:
        for obj in collection.objects:
            bpy.data.objects.remove(obj, do_unlink=True)
        bpy.data.collections.remove(collection)
    for rem_mesh in bpy.data.meshes:
        if rem_mesh.users == 0:
            bpy.data.meshes.remove(rem_mesh)
    # the blender does not have a single solution for cleaning the scene. this method was invented to try to clean up the scene in any way =\
    if len(bpy.data.objects) > 0:
        for obj in bpy.data.objects:
            bpy.data.objects.remove(obj)
        scene_clear()

    # restore animation data to default
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
                # if modifier.type == 'SUBSURF':
                bpy.ops.object.modifier_apply(modifier=modifier.name)
                # apply transformations
                bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
                triangulate(sel)

    # copy empty components
    pass


def get_donor_acceptor(context: bpy.types.Context) -> [bpy.types.Object, bpy.types.Object]:
    active = context.active_object
    if active is None:
        return None, None
    acceptor = active
    selected = context.selected_objects
    acceptors = list(filter(lambda x: x != active, selected))
    if len(acceptors) != 1:
        return None, acceptor
    donor = acceptors[0]
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


def get_frame_range(context, obj):
    is_use_mesh_frame_range = context.scene.is_use_mesh_frame_range
    report_info(f'Use mesh frame range: {is_use_mesh_frame_range}')
    if is_use_mesh_frame_range:
        # TODO: try multiple objects?
        frame_range = get_object_frame_range(obj)
        while frame_range is None and obj.parent is not None:
            frame_range = get_object_frame_range(obj.parent)
    else:
        frame_range = context.scene.frame_start, context.scene.frame_end
    return frame_range


def animation_to_shapekey(context, donor, acceptor):
    acceptor.shape_key_clear()
    acceptor.shape_key_add(name='basis', from_mix=False)
    depgraph = context.evaluated_depsgraph_get()
    n_vertex = len(donor.data.vertices)

    frame_range = get_frame_range(context, donor)
    frame_start, frame_end = frame_range
    # frame_data = np.zeros((n_vertex * 3), np.float32)
    for frame in range(frame_start, frame_end + 1):
        context.scene.frame_set(frame)
        # animate vertices
        donor_bm = bmesh.new()
        donor_bm.from_object(donor, depgraph)
        donor_bm.verts.ensure_lookup_table()
        # donor_bm.verts.foreach_get('co', frame_data)
        frame_data = np.array([x for vertex in donor_bm.verts for x in vertex.co])
        # copy verts from donor to acceptor
        new_key = acceptor.shape_key_add(name=str(frame), from_mix=False)
        new_key.data.foreach_set('co', frame_data)

        # bpy.ops.object.transform_apply(location=True, rotation=True, scale=False)
        # for i, vertex in enumerate(donor_verts):
        #     new_key.data[i].co = vertex.co
        #     vertex: bmesh.types.BMVert
        # new_key.data[i].co = donor.matrix_world @ vertex.co

        # bpy.ops.transform.transform(value=(donor.location.x,donor.location.y,donor.location.z, 1))
        insert_keyframe(new_key, frame)


def animation_skeletal(context):
    donor, acceptor = get_donor_acceptor(context)
    armature = donor
    acceptor.shape_key_clear()

    isSkeletal = bpy.context.scene.skeletal
    if not isSkeletal:
        base_key = acceptor.shape_key_add(name='basis', from_mix=False)

    depgraph = context.evaluated_depsgraph_get()
    for frame in range(context.scene.frame_start, context.scene.frame_end + 1):
        context.scene.frame_set(frame)
        if not isSkeletal:
            # animate vertices
            donor_bm = bmesh.new()
            donor_bm.from_object(donor, depgraph)
            donor_bm.verts.ensure_lookup_table()
            # donor_verts = donor.data.vertices
            donor_verts = donor_bm.verts

            # copy verts from donor to acceptor
            new_key = acceptor.shape_key_add(name=str(frame), from_mix=False)

            # bpy.ops.object.transform_apply(location=True, rotation=True, scale=False)
            for i, vertex in enumerate(donor_verts):
                new_key.data[i].co = vertex.co
                vertex: bmesh.types.BMVert
                # new_key.data[i].co = donor.matrix_world @ vertex.co

            # bpy.ops.transform.transform(value=(donor.location.x,donor.location.y,donor.location.z, 1))
            insert_keyframe(new_key, frame)

        if isSkeletal:
            # acceptor.rotation_euler[0] = -armature.rotation_euler[1]-0.385398-0.16
            # acceptor.rotation_euler[0] = -armature.rotation_euler[1]*2-0.385398-0.16

            #        acceptor.rotation_euler[0] = -armature.rotation_euler[1]-0.385398-0.16
            #        acceptor.rotation_euler[1] = armature.rotation_euler[0]
            #        acceptor.rotation_euler[2] = armature.rotation_euler[2]+1.570796
            acceptor.rotation_quaternion[0] = armature.rotation_quaternion[0]
            acceptor.rotation_quaternion[1] = armature.rotation_quaternion[1]
            acceptor.rotation_quaternion[2] = armature.rotation_quaternion[2]
            acceptor.rotation_quaternion[3] = armature.rotation_quaternion[3]

            # acceptor.rotation_euler[2] = armature.rotation_euler[2]-1.570796-1.570796
            acceptor.keyframe_insert(data_path='rotation_quaternion', index=-1)

            # acceptor.location[0] = armature.location[0]/100+0.028571

            #        acceptor.location[0] = armature.location[0]+2.8571/100
            #        acceptor.location[1] = armature.location[1]
            #        acceptor.location[2] = (armature.location[2]/100+ (0.08+8)/100)
            acceptor.location[0] = armature.location[0]
            acceptor.location[1] = armature.location[1]
            acceptor.location[2] = armature.location[2]

            acceptor.keyframe_insert(data_path='location', index=-1)

            # acceptor.scale = donor.scale*100
            # acceptor.scale = [1,1,1]
            acceptor.scale = donor.scale

            # acceptor.transform_apply(location=False, rotation=False, scale=True)
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


def copy_collection(copy_from_name, copy_to_name, name_prefix=None, replace=True):
    from_collection = bpy.data.collections.get(copy_from_name)
    # make new collection
    to_collection = get_collection(copy_to_name)

    if replace and to_collection is not None:
        clear_collection(copy_to_name)
        to_collection = None

    if to_collection is None:
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


def create_morph_items(base_collection, morph_collection, morph_prefix, include_meshes=None):
    for obj in base_collection.objects:
        if obj.type != 'MESH':
            continue
        if include_meshes and obj.name not in include_meshes:
            continue
        # добавляем коллекции
        morph_name = morph_prefix + obj.name
        if morph_name in morph_collection.objects:
            bpy.data.objects.remove(morph_collection.objects.get(morph_name))
        # копируем меши
        new_obj = obj.copy()
        new_obj.name = morph_name
        new_obj.data = obj.data.copy()
        new_obj.data.name = new_obj.name
        morph_collection.objects.link(new_obj)


def create_all_morphs(context, include_meshes=None):
    # Триангулируем и применяем модификаторы на базовой модели
    bAutofix = context.scene.auto_apply
    if bAutofix:
        auto_fix_scene()

    if not include_meshes:
        clear_morph_collections(start_index=1)

    links = dict()
    base_collection = get_collection("base")

    # objects = [base_collection.get(name) for name in include_meshes] if include_meshes else base_collection.objects

    for obj in base_collection.objects:
        if obj.type != 'MESH':
            continue
        if include_meshes and obj.name not in include_meshes:
            continue
        links[obj.name] = obj.parent.name if obj.parent else None
        # clear animation from base object. TODO: create copies to preserve animation?
        obj.animation_data_clear()
        obj.shape_key_clear()

    ensure_morph_collections()

    for morph_name, morph_prefix in zip(MODEL().morph_collection[1:], list(MODEL().morph_comp.values())[1:]):
        collection = bpy.data.collections.get(morph_name)
        create_morph_items(base_collection, collection, morph_prefix, include_meshes)

    scene = context.scene
    scaled = scene.scaled
    vectors = [
        (scene.s_s_x, scene.s_s_y, scene.s_s_z),
        (scene.s_d_x, scene.s_d_y, scene.s_d_z),
        (scene.s_u_x, scene.s_u_y, scene.s_u_z),
        (scaled, scaled, scaled),
        (scaled + scene.s_s_x - 1, scaled + scene.s_s_y - 1, scaled + scene.s_s_z - 1),
        (scaled + scene.s_d_x - 1, scaled + scene.s_d_y - 1, scaled + scene.s_d_z - 1),
        (scaled + scene.s_u_x - 1, scaled + scene.s_u_y - 1, scaled + scene.s_u_z - 1),
    ]

    # привязываем родителей
    for s in range(1, 8):
        for child, parent in links.items():
            if parent is None:
                continue
            bpy.data.objects[MODEL().morph_comp[s] + child].parent = bpy.data.objects[
                MODEL().morph_comp[s] + parent]

    # Трогаем только scaled коллекции
    for s in range(1, 8):
        for child, parent in links.items():
            if parent is None:
                bpy.data.objects[MODEL().morph_comp[s] + child].scale = vectors[s - 1]

    bpy.ops.object.select_all(action='DESELECT')
    for i in range(0, 8):
        coll_name = MODEL().morph_collection[i]
        coll = bpy.data.collections.get(coll_name)
        for obj in coll.objects:
            if include_meshes and obj.name not in include_meshes:
                continue
            obj.select_set(True)
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    bpy.ops.object.select_all(action='DESELECT')


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


def get_object_frame_range(obj):
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


def get_collection_frame_range(collection_name):
    coll = get_collection(collection_name)
    obj = get_root_objects(coll.objects)
    return get_object_frame_range(obj)


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

    if not to_process:
        report_info(f"Done - nothing to do")
        return

    is_use_mesh_frame_range = context.scene.is_use_mesh_frame_range
    report_info(f'Use mesh frame range: {is_use_mesh_frame_range}')
    if is_use_mesh_frame_range:
        # TODO: try multiple objects?
        frame_range = get_object_frame_range(to_process[0])
    else:
        frame_range = context.scene.frame_start, context.scene.frame_end

    if frame_range is None:
        report_info(f"Couldn't determine frame range from mesh.", icon="ERROR")
        return

    frame_start, frame_end = frame_range
    report_info(f"Baking transform from frame {frame_start} to {frame_end}")
    # prepare
    context.scene.frame_set(999)
    pairs = []
    for obj in to_process:
        donor, acceptor = bake_make_acceptor(context, obj)
        pairs.append((donor, acceptor))
    # main run
    for frame in range(frame_start, frame_end + 1):
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


def export_animation(context, frame_range, animation_source_name, res_path):
    animation_name = context.scene.animation_name
    model_name = context.scene.figmodel_name

    links = collect_links(animation_source_name)
    animations = collect_animations(frame_range, animation_source_name)
    blender2abs_rotations(links, animations)
    abs2ei_rotations(links, animations)

    write_animations(animations, res_path, model_name, animation_name)


def write_animations(animations, res_path, model_name, animation_name):
    # pack current animation first. byte array for each part (lh1, lh2, etc)
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

    data[animation_name] = anm_res.getvalue()  # modified animation set

    # write animations into res file
    with (
        ResFile(res_path, "a") as figres,
        figres.open(export_model_name, "w") as anmfile,
        ResFile(anmfile, "w") as res
    ):
        for name, anm_data in data.items():
            with res.open(name, "w") as file:
                file.write(anm_data)

    print(res_path + 'saved')


def ue4_toolchain(operator, context):
    def check_type(obj, type_needed):
        if obj.type != type_needed:
            raise Exception("Incorrect selection: need to select root of root->armature->mesh hierarchy")

    root = context.active_object
    check_type(root, "EMPTY")
    armature = root.children[0]
    check_type(armature, "ARMATURE")
    mesh = armature.children[0]
    check_type(mesh, "MESH")
    ue4_toolchain_(operator, context, root, armature, mesh)


def animation_euler_to_quaternions(obj: bpy.types.Object):
    action = obj.animation_data.action
    frames, eulers = get_euler_frames(action)
    quaternions = [euler_to_quaternion(*euler) for euler in eulers]
    # rebase animation from first frame
    # bq = quaternions[0]
    # ibq = bq.inverted()
    # quaternions = [q * ibq for q in quaternions]
    # bpy.ops.object.select_all(action='DESELECT')
    # obj.select_set(True)
    # obj.rotation_mode = 'QUATERNION'
    # obj.rotation_quaternion = ibq
    # bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)
    ###
    animation_from_quaternions(obj, frames, quaternions)


def euler_to_quaternion(x, y, z):
    euler = Euler((x, y, z), 'XYZ')
    quaternion = euler.to_quaternion()
    return quaternion


def get_euler_frames(action: bpy.types.Action):
    x_curve = action.fcurves.find('rotation_euler', index=0)
    y_curve = action.fcurves.find('rotation_euler', index=1)
    z_curve = action.fcurves.find('rotation_euler', index=2)

    if not x_curve: return [], []
    keyframe_points = x_curve.keyframe_points

    frames = []
    eulers = []
    for key in keyframe_points:
        frame = key.co[0]
        x_rot = x_curve.evaluate(frame)
        y_rot = y_curve.evaluate(frame)
        z_rot = z_curve.evaluate(frame)
        frames.append(frame)
        euler = (x_rot, y_rot, z_rot)
        eulers.append(euler)
    return frames, eulers


def animation_from_quaternions(obj, frames, quaternions):
    obj.rotation_mode = 'QUATERNION'
    for frame, q in zip(frames, quaternions):
        obj.rotation_quaternion = q
        obj.keyframe_insert(data_path="rotation_quaternion", frame=frame)
        # obj.keyframe_insert(data_path="rotation_quaternion", frame=frame, index=0, value=q[0])
        # obj.keyframe_insert(data_path="rotation_quaternion", frame=frame, index=1, value=q[1])
        # obj.keyframe_insert(data_path="rotation_quaternion", frame=frame, index=2, value=q[2])
        # obj.keyframe_insert(data_path="rotation_quaternion", frame=frame, index=3, value=q[3])


def remove_scale_furve(obj):
    action = obj.animation_data.action
    for i in range(3):
        fcurve = action.fcurves.find("scale", index=i)
        if not fcurve:
            break
        action.fcurves.remove(fcurve)
    bpy.ops.object.select_all(action='DESELECT')
    # rescale object
    # assume curve scale was 0.01
    scale = 0.01
    obj.scale = (scale, scale, scale)
    obj.select_set(True)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)


def ue4_toolchain_(operator, context, root, armature, mesh):
    bpy.ops.object.select_all(action='DESELECT')
    root.select_set(True)
    mesh.select_set(True)
    bpy.ops.object.transform_apply()
    operator.report({"INFO"}, "Applied transforms to root and mesh")
    new_mesh: bpy.types.Object = mesh.copy()
    new_mesh.animation_data_clear()
    new_mesh.data = mesh.data.copy()
    new_mesh.parent = None
    context.scene.collection.objects.link(new_mesh)
    operator.report({"INFO"}, "Copy and unparent mesh")
    new_mesh.modifiers.clear()
    operator.report({"INFO"}, "Clear modifiers on new object")

    new_mesh.animation_data_clear()
    new_mesh.animation_data_create()
    action = armature.animation_data.action.copy()
    new_mesh.animation_data.action = action
    operator.report({"INFO"}, "Link armature animation data to mesh")
    animation_to_shapekey(context, mesh, new_mesh)
    operator.report({"INFO"}, "Shapekeying animation from old mesh to new mesh")
    animation_euler_to_quaternions(new_mesh)
    operator.report({"INFO"}, "Convert euler animation to quaternion")
    # transfer transform
    new_mesh.scale = armature.scale
    new_mesh.location = armature.location
    if armature.rotation_mode == "XYZ":
        new_rot_q = euler_to_quaternion(*armature.rotation_euler)
    else:
        new_rot_q = armature.rotation_quaternion
    new_mesh.rotation_quaternion = new_rot_q
    remove_scale_furve(new_mesh)
    operator.report({"INFO"}, "Clear scale animation")


def repack_resfile(path):
    importlib.reload(resfile)
    with ResFile(path, 'r') as res:
        data = res.get_valid_data(recursive=True)

    with open(path, "wb") as f:
        f.write(data)
