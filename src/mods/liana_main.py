import sys
import os
import subprocess
import bpy

from bpy.types import Mesh
from contextlib import redirect_stdout
from sys import stdout
from io import StringIO
from math import *
from .liana.helpers import *
from .liana.blender import *
from .liana.valorant import *
from .liana.importer_xay import *

logger = setup_logger(__name__)

try:
    sys.dont_write_bytecode=True
    from ..tools.injector import inject_dll
except:
    pass

object_types = []

SELECTIVE_OBJECTS = []
SELECTIVE_UMAP = [
    # "Pitt_Art_VFX"
    # "Ascent_Art_A",
    #"Ascent_Art_APathMid",
    # "Ascent_Art_Atk",
    # "Ascent_Art_AtkPathA",
    # "Ascent_Art_AtkPathB",
    # "Ascent_Art_B",
    #"Ascent_Art_Def",
    #"Ascent_Art_DefPathA",
    #"Ascent_Art_DefPathB",
    # "Ascent_Art_Env_VFX",
    #"Ascent_Art_Mid",
    # "Ascent_Art_Vista",
    # "Ascent_Art_VistaA",
    # "Ascent_Art_VistaAtk",
    # "Ascent_Art_VistaB",
    # "Ascent_Art_VistaDef",
    # "Ascent_Gameplay",
    # "Ascent_Lighting"
]
BLACKLIST = [
    "navmesh",
    "_breakable",
    "_collision",
    "windstreaks_plane",
    "sm_port_snowflakes_boundmesh",
    "sm_barrierduality",
    "M_Pitt_Caustics_Box",
    "box_for_volumes", 
    "BombsiteMarker_0_BombsiteA_Glow",
    "BombsiteMarker_0_BombsiteB_Glow",
    "supergrid",
    "_col",
    "M_Pitt_Lamps_Glow",
    "for_volumes",
    "Bombsite_0_ASiteSide",
    "Bombsite_0_BSiteSide",
    "For_Volumes",
    "Foxtrot_ASite_Plane_DU",
    "Foxtrot_ASite_Side_DU",
    "BombsiteMarker_0_BombsiteA_Glow",
    "BombsiteMarker_0_BombsiteB_Glow",
    "Tech_0_RebelSupplyCargoTarpLargeCollision"
]

COUNT = 0


# TODO DELETE THESE

ScalarParameterValues = []
StaticParameterValues = []
TextureParameterValues = []
BasePropertyOverrides = {}
VectorParameterValues = []
OtherTypes = []
MaterialTypes = []

PROPS = {
    "ScalarParameterValues": ScalarParameterValues,
    "Static": StaticParameterValues,
    "TextureParameterValues": TextureParameterValues,
    "BasePropertyOverrides": BasePropertyOverrides,
    "Vector": VectorParameterValues,
}
object_types = []
stdout = StringIO()


def extract_assets(settings: Settings):
    assetobjects = settings.selected_map.folder_path.joinpath("all_assets.txt")
    args = [settings.umodel.__str__(),
            f"-path={settings.paks_path.__str__()}",
            "-game=valorant",
            f"-aes={settings.aes}",
            f"-files={assetobjects}",
            "-export",
            "-xay",
            "-noanim",
            "-nooverwrite",
            f"-{settings.texture_format.replace('.', '')}",
            f"-out={settings.assets_path.__str__()}"]

    # Export Models
    subprocess.call(args,
                    stderr=subprocess.DEVNULL)


def extract_data(settings: Settings, export_directory: str, asset_list_txt: str = ""):

    args = [settings.cue4extractor.__str__(),
            "--game-directory", settings.paks_path.__str__(),
            "--aes-key", settings.aes,
            "--export-directory", export_directory.__str__(),
            "--map-name", settings.selected_map.name,
            "--file-list", asset_list_txt,
            "--game-umaps", settings.umap_list_path.__str__()
            ]

    subprocess.call(args)


def search_object(map_object, index, link) -> bpy.types.Object:
    # obj = bpy.data.objects.get(map_object.name)
    # if obj:
    #     logger.info(f"[{index}] | Duplicate : {shorten_path(map_object.model_path, 4)} - {map_object.uname}")
    #     master_object = obj.copy()  # duplicate(obj, data=False)
    #     master_object.name = map_object.uname
    #     reset_properties(master_object)
    #     return master_object
    for source_object in bpy.data.objects:
        a = source_object.name.rpartition('_')
        # print(a)
        if map_object.name in source_object.type == "MESH":
            logger.info(f"[{index}] | Duplicate : {shorten_path(map_object.model_path, 4)} - {map_object.uname}")

            master_object = duplicate(source_object, data=False)
            master_object.name = map_object.uname
            # master_object.data.materials.clear()

            link(master_object)
            reset_properties(master_object)
            return master_object
    return False


def get_object(map_object, index, link, scene_unlink) -> bpy.types.Object:

    master_object = search_object(map_object, index, link)

    if not master_object:
        logger.info(f"[{index}] | Importing : {shorten_path(map_object.model_path, 4)} - {map_object.uname}")
        with redirect_stdout(stdout):
            master_object = xay(map_object.model_path)
        # master_object = bpy.context.active_object
        master_object.name = map_object.uname

    try:
        link(master_object)
        # scene_unlink(master_object)
    except:
        pass

    return master_object


def get_map_assets(settings: Settings):
    umaps = []
    if check_export(settings):
        # if 1 == 1:
        logger.info("Extracting JSON files")
        extract_data(settings, export_directory=settings.selected_map.umaps_path)

        umaps = get_files(path=settings.selected_map.umaps_path.__str__(), extension=".json")
        umap: Path
        object_list = list()
        materials_ovr_list = list()
        materials_list = list()

        for umap in umaps:
            umap_json, asd = filter_umap(read_json(umap))
            object_types.append(asd)

            # save json
            save_json(umap.__str__(), umap_json)

            # get objects
            umap_objects, umap_materials = get_objects(umap_json)

            object_list.append(umap_objects)
            materials_ovr_list.append(umap_materials)

            # parse objects

        object_txt = save_list(filepath=settings.selected_map.folder_path.joinpath("_assets_objects.txt"), lines=object_list)
        mats_ovr_txt = save_list(filepath=settings.selected_map.folder_path.joinpath("_assets_materials_ovr.txt"), lines=materials_ovr_list)

        extract_data(settings, export_directory=settings.selected_map.objects_path, asset_list_txt=object_txt)
        extract_data(settings, export_directory=settings.selected_map.materials_ovr_path, asset_list_txt=mats_ovr_txt)

        # ---------------------------------------------------------------------------------------

        models = get_files(path=settings.selected_map.objects_path.__str__(), extension=".json")
        model: Path
        for model in models:
            model_json = read_json(model)[2]
            model_name = model.stem

            # save json
            save_json(model.__str__(), model_json)

            # get object materials
            model_materials = get_object_materials(model_json)

            # get object textures
            # ...

            materials_list.append(model_materials)
        save_list(filepath=settings.selected_map.folder_path.joinpath("all_assets.txt"), lines=[
            [
                path_convert(path) for path in _list
            ] for _list in object_list + materials_list + materials_ovr_list
        ])
        mats_txt = save_list(filepath=settings.selected_map.folder_path.joinpath("_assets_materials.txt"), lines=materials_list)
        extract_data(settings, export_directory=settings.selected_map.materials_path, asset_list_txt=mats_txt)
        extract_assets(settings)
        with open(settings.selected_map.folder_path.joinpath('exported.yo').__str__(), 'w') as out_file:
            out_file.write(write_export_file())
    else:
        umaps = get_files(path=settings.selected_map.umaps_path.__str__(), extension=".json")
        logger.info("JSON files are already extracted")

    return umaps

# TODO : MATERIALS

def set_materials(settings: Settings, byo: bpy.types.Object, map_object: MapObject, decal: bool = False):
    if decal:
        if "DecalMaterial" in map_object["Properties"]:

            yoyo = map_object["Properties"]["DecalMaterial"]

            mat_name = get_object_name(data=yoyo, mat=True)
            mat_json = read_json(settings.selected_map.materials_ovr_path.joinpath(f"{mat_name}.json"))

            mat = bpy.data.materials.new(name="Material")
            byo.data.materials.append(mat)

            byoMAT = byo.material_slots[0].material
            set_material(settings=settings, mat=byoMAT, mat_data=mat_json[0], object=map_object, decal=True)

            return
    else:
        object_properties_OG = map_object.json["Properties"]
        object_properties = map_object.data["Properties"]

        if "StaticMaterials" in object_properties_OG:
            for index, mat in enumerate(object_properties_OG["StaticMaterials"]):
                if type(mat["MaterialInterface"]) is dict:
                    mat_name = get_object_name(data=mat["MaterialInterface"], mat=True)
                    if "WorldGridMaterial" not in mat_name:
                        mat_json = read_json(settings.selected_map.materials_path.joinpath(f"{mat_name}.json"))
                        try:
                            obj_data = byo.data
                            mat_data = mat_json[0]

                            if getattr(obj_data, VCOL_ATTR_NAME):
                                mat_name = mat_data["Name"] + "_V"
                            else:
                                mat_name = mat_data["Name"] + "_NV"

                            byoMAT = bpy.data.materials.get(mat_name)
                            if byoMAT is None:
                                byoMAT = bpy.data.materials.new(name=mat_name)
                                set_material(
                                    settings=settings, mat=byoMAT, mat_data=mat_json[0], object_cls=map_object, object_byo=byo)

                            byo.material_slots[index].material = byoMAT
                            # byoMAT = bpy.data.materials.new(name=mat_name)
                            # byo.material_slots[index].material = byoMAT
                            # set_material(settings=settings, mat=byoMAT, mat_data=mat_json[0], object_cls=map_object, object_byo=byo)
                        except IndexError:
                            pass

        if "OverrideMaterials" in object_properties:
            for index, mat in enumerate(object_properties["OverrideMaterials"]):
                if type(mat) is dict:
                    mat_name = get_object_name(data=mat, mat=True)
                    mat_json = read_json(settings.selected_map.materials_ovr_path.joinpath(f"{mat_name}.json"))
                    try:
                        obj_data = byo.data
                        mat_data = mat_json[0]

                        if getattr(obj_data, VCOL_ATTR_NAME):
                            mat_name = mat_data["Name"] + "_V"
                        else:
                            mat_name = mat_data["Name"] + "_NV"

                        byoMAT = bpy.data.materials.get(mat_name)
                        if byoMAT is None:
                            byoMAT = bpy.data.materials.new(name=mat_name)
                            set_material(
                                settings=settings, mat=byoMAT, mat_data=mat_json[0], object_cls=map_object, object_byo=byo)

                        byo.material_slots[index].material = byoMAT
                        # byoMAT = bpy.data.materials.new(name=mat_name)
                        # byo.material_slots[index].material = byoMAT
                        # if byoMAT is not None:
                        #     set_material(settings=settings, mat=byoMAT, mat_data=mat_json[0], override=True, object_cls=map_object, object_byo=byo)
                    except IndexError:
                        pass

# SECTION : Set Material

def set_material(settings: Settings, mat: bpy.types.Material, mat_data: dict, override: bool = False, decal: bool = False, object_cls: MapObject = None, object_byo: bpy.types.Object = None):

    mat.use_nodes = True



    # define shits
    # define shits
    nodes = mat.node_tree.nodes
    link = mat.node_tree.links.new
    create_node = nodes.new

    obj_data = object_byo.data

    if "Properties" not in mat_data:
        return

    mat_props = mat_data["Properties"]

    if "Parent" in mat_props:
        mat_type = get_name(mat_props["Parent"]["ObjectPath"])
    else:
        mat_type = "NO PARENT"

    if "PhysMaterial" in mat_props:
        mat_phys = get_name(mat_props["PhysMaterial"]["ObjectPath"])
        if "M_Glass" == mat_phys and "Emissive" not in mat.name:
            mat_type = "Glass"
    else:
        mat_phys = False

    # Clear Nodes
    clear_nodes(nodes)

    N_OUTPUT = nodes['Material Output']

    # EnvCollision
    if "EnvCollision_MAT" in mat_type:
        bpy.data.objects.remove(object_byo)

    N_SHADER = nodes.new("ShaderNodeGroup")
    N_MAPPING = None

    # Pre Overrides

    types_base = [
        "BaseEnv_MAT_V4",
        "BaseEnv_MAT_V4_Fins",
        "BaseEnv_MAT_V4_Inst",
        "BaseEnvUBER_MAT_V3_NonshinyWall",
        "BaseEnv_MAT_V4_Foliage",
        "BaseEnv_MAT_V4_VFX",
        "BaseEnv_MAT",
        "BaseEnv_MAT_V4_ShadowAsTranslucent",
        "Mat_BendingRope",
        "FoliageEnv_MAT",
        "BaseOpacitySpecEnv_MAT",
        "BaseEnv_ClothMotion_MAT",
        "BaseEnvVertexAlpha_MAT",
        "Wood_M6_MoroccanTrimA_MI",
        "Stone_M0_SquareTiles_MI",
        "BaseEnv_MAT_V4_Rotating",
        "HorizontalParallax",
        "TileScroll_Mat",
        "BasaltEnv_MAT",
        "BaseEnvEmissive_MAT",
        "BaseEnvEmissiveUnlit_MAT",
        "BaseEnv_Unlit_MAT_V4"
    ]

    types_blend = [
        "BaseEnv_Blend_UV1_MAT_V4",
        "BaseEnv_Blend_UV2_MAT_V4",
        "BaseEnv_Blend_UV3_MAT_V4",
        "BaseEnv_Blend_UV4_MAT_V4",
        "BaseEnv_Blend_MAT_V4_V3Compatibility",
        "BaseEnv_Blend_MAT_V4",
        "BaseEnv_BlendNormalPan_MAT_V4",
        "BaseEnv_Blend_UV2_Masked_MAT_V4",
        "BlendEnv_MAT"
        "MaskTintEnv_MAT"
    ]

    types_glass = [
        "Glass"
    ]

    types_emissive = [
        "BaseEnv_Unlit_Texture_MAT_V4",
    ]

    types_emissive_scroll = [
        "BaseEnvEmissiveScroll_MAT",
    ]

    types_screen = [
        "BaseEnvEmissiveLCDScreen_MAT"
    ]

    types_hologram = [
        "BaseEnv_HologramA"
    ]

    types_decal = [
        "BaseOpacity_RGB_Env_MAT"
    ]

    types_lightshift = [
        "0_GeoLightShaft",
        "0_GenericA01_MAT",
        "MI_OrangeKingdom_LightShaft"
    ]

    types_spriteglow = [
        "0_Sprite_GlowLight",
    ]

    types_waterfallvista = [
        "0_Waterfall_Base1"
    ]
    
    types_ventsmoke = [
        "0_VentSmoke_Duo",
        "0_VentSmoke"
    ]

    MaterialTypes.append(mat_type)

    blend_mode = BlendMode.OPAQUE

    mat_switches = []
    mat_colors = {}
    mat_shading_model = "MSM_AresEnvironment"

    
    if mat_type in types_decal:
        N_SHADER.node_tree = get_valorant_shader(group_name="VALORANT_Decal")
        
    elif"Blend" in mat_type:
        N_SHADER.node_tree = get_valorant_shader(group_name="VALORANT_Blend") #VALORANT_Blend
        user_mat_type = "Blend"

    elif mat_type == "NO PARENT":
        if "Sky" not in mat.name:
            N_SHADER.node_tree = get_valorant_shader(group_name="VALORANT_Base")
        elif "Sky" in mat.name:
            N_SHADER.node_tree = get_valorant_shader(group_name="VALORANT_Skybox")
    elif mat_type in types_base:
        N_SHADER.node_tree = get_valorant_shader(group_name="VALORANT_Base")
    else:
        N_SHADER.node_tree = get_valorant_shader(group_name="VALORANT_Base")
    #link shader output to Mat
    link(N_SHADER.outputs[0], N_OUTPUT.inputs[0])

    # BASE PROPERTY OVERRIDES
    if "BasePropertyOverrides" in mat_props:
        for prop_name, prop_value in mat_props["BasePropertyOverrides"].items():

            # ANCHOR Shading Model
            if "ShadingModel" == prop_name:
                if "MSM_AresEnvironment" in prop_value:
                    pass
                if "MSM_Unlit" in prop_value:
                    pass

            # ANCHOR Blend Mode
            if "BlendMode" == prop_name:
                if "BLEND_Translucent" in prop_value:
                    blend_mode = BlendMode.BLEND
                elif "BLEND_Masked" in prop_value:
                    blend_mode = BlendMode.CLIP
                elif "BLEND_Additive" in prop_value:
                    blend_mode = BlendMode.BLEND
                elif "BLEND_Modulate" in prop_value:
                    blend_mode = BlendMode.BLEND
                elif "BLEND_AlphaComposite" in prop_value:
                    blend_mode = BlendMode.BLEND
                elif "BLEND_AlphaHoldout" in prop_value:
                    blend_mode = BlendMode.CLIP
            # -----------------------------------------------
            # LOGGING
            if prop_name not in BasePropertyOverrides:
                BasePropertyOverrides[prop_name] = []
            BasePropertyOverrides[prop_name].append(mat_props["BasePropertyOverrides"][prop_name])
            BasePropertyOverrides[prop_name] = list(dict.fromkeys(BasePropertyOverrides[prop_name]))
    # OPACITY
    if "Alpha" in N_SHADER.inputs:
        scalar_node = mat.node_tree.nodes.new(type="OctaneGreyscaleColor")
        scalar_node.label = "Alpha"
        if blend_mode == BlendMode.CLIP or blend_mode == BlendMode.BLEND:
            scalar_node.a_value = 0
        else:
            scalar_node.a_value = 1
        #if "Glass" in user_mat_type:
        #    scalar_node.a_value = 0.5
        link(scalar_node.outputs[0], N_SHADER.inputs["Alpha"])
    # VERTEX COLORS
    if "vertex color" in N_SHADER.inputs:
        vertex_color_node = mat.node_tree.nodes.new(type="OctaneColorVertexAttribute")
        vertex_color_node.inputs[0].default_value = "PSKVTXCOL_0"
        link(vertex_color_node.outputs[0], N_SHADER.inputs["vertex color"])
    if "vertex alpha" in N_SHADER.inputs:
        vertex_alpha_node = mat.node_tree.nodes.new(type="OctaneColorVertexAttribute")
        vertex_alpha_node.inputs[0].default_value = "PSKVTXCOL_0_ALPHA"
        link(vertex_alpha_node.outputs[0], N_SHADER.inputs["vertex alpha"])
    #PARAMS
    if "StaticParameters" in mat_props:
        if "StaticSwitchParameters" in mat_props["StaticParameters"]:
            for param in mat_props["StaticParameters"]["StaticSwitchParameters"]:
                param_name = param["ParameterInfo"]["Name"].lower()
                if param_name in N_SHADER.inputs:
                    scalar_node = mat.node_tree.nodes.new(type="OctaneGreyscaleColor")
                    scalar_node.label = param_name
                    if (param["Value"] == "true"):
                        scalar_node.a_value = 1.0
                    else:
                        scalar_node.a_value = 0.0
                    link(scalar_node.outputs[0], N_SHADER.inputs[param_name])

                # LOGGING
                StaticParameterValues.append(param_name)

        if "StaticComponentMaskParameters" in mat_props["StaticParameters"]:
            for param in mat_props["StaticParameters"]["StaticComponentMaskParameters"]:
                param_name = param["ParameterInfo"]["Name"].lower()
                if param_name in N_SHADER.inputs:
                    if param_name == "mask":
                        colors = {"R", "G", "B", "A"}
                        for color in colors:
                            if color in param:
                                if param[color]:
                                    scalar_node = mat.node_tree.nodes.new(type="OctaneGreyscaleColor")
                                    scalar_node.label = f"Use {color}"
                                    scalar_node.a_value = 1
                                    link(scalar_node.outputs[0], N_SHADER.inputs[f"Use {color} for {param_name}"])

    if "ScalarParameterValues" in mat_props:
        pos = [-300, 0]
        index = 0
        for param in mat_props["ScalarParameterValues"]:
            param_name = param['ParameterInfo']['Name'].lower()
            if param_name in N_SHADER.inputs:
                scalar_node = mat.node_tree.nodes.new(type="OctaneGreyscaleColor")
                if (param_name == "mask blend power" or param_name == "normal mask blend power"):
                    scalar_node.a_value = param["ParameterValue"]/100
                else:
                    scalar_node.a_value = param["ParameterValue"]
                scalar_node.label = param_name
                pos[1] = index * -100
                index += 1
                scalar_node.location[0] = pos[0]
                scalar_node.location[1] = pos[1]
                link(scalar_node.outputs[0], N_SHADER.inputs[param_name])
            # LOGGING
            ScalarParameterValues.append(param_name)

    if "VectorParameterValues" in mat_props:
        pos = [-600, 0]
        index = 0
        for param in mat_props["VectorParameterValues"]:
            param_name = param['ParameterInfo']['Name'].lower()
            if param_name in N_SHADER.inputs:
                param_value = param["ParameterValue"]
                color_node = nodes.new(type="OctaneRGBColor")
                color_node.a_value = get_rgb_no_alpha(param_value)
                color_node.label = param_name
                pos[1] = index * -100
                index += 1
                color_node.location[0] = pos[0]
                color_node.location[1] = pos[1]
                link(color_node.outputs[0], N_SHADER.inputs[param_name])
            # LOGGING
            VectorParameterValues.append(param_name)

    if "TextureParameterValues" in mat_props:
        pos = [-1000, 0]
        index = 0
        blacklist_tex = [
        "Albedo_DF",
        "MRA_MRA",
        "Normal_NM",
        "Diffuse B Low",
        "Blank_M0_NM",
        "Blank_M0_Flat_00_black_white_DF",
        "Blank_M0_Flat_00_black_white_NM",
        "flatnormal",
        "flatwhite",
        "Basalt_0_M0_Edging_DF",
        ]
        for param in mat_props["TextureParameterValues"]:
            param_name = param['ParameterInfo']['Name'].lower()
            if param_name in N_SHADER.inputs:
                tex_game_path = get_texture_path(s=param, f=settings.texture_format)
                tex_local_path = settings.assets_path.joinpath(tex_game_path).__str__()
                tex_name = Path(tex_local_path).stem
                if Path(tex_local_path).exists() and tex_name not in blacklist_tex:
                    tex_image_node = mat.node_tree.nodes.new('OctaneRGBImage')
                    tex_image_node.image = get_image(tex_name, tex_local_path)
                    tex_image_node.label = param_name
                    pos[1] = index * -400
                    index += 1
                    tex_image_node.location[0] = pos[0]
                    tex_image_node.location[1] = pos[1]
                    tex_image_node.inputs[2].default_value = 1.0
                    if 'diffuse' in param_name: tex_image_node.inputs[2].default_value = 2.2
                    link(tex_image_node.outputs[0], N_SHADER.inputs[param_name])
                    #for textures that have alpha
                    if f"{param_name}_alpha" in N_SHADER.inputs:
                        tex_image_node_alpha = mat.node_tree.nodes.new('OctaneAlphaImage')
                        tex_image_node_alpha.image = get_image(tex_name, tex_local_path)
                        tex_image_node_alpha.label = f"{param_name}_alpha"
                        link(tex_image_node_alpha.outputs[0], N_SHADER.inputs[ f"{param_name}_alpha"])
                # LOGGING
                TextureParameterValues.append(param_name)
    #DEFAULT PARAMS
    def set_default(name, value):
        color_node = mat.node_tree.nodes.new(type="OctaneRGBColor")
        color_node.a_value = value
        color_node.label = name
        link(color_node.outputs[0], N_SHADER.inputs[name])
    default_params = [
    ("diffuse", (1, 1, 1)),
    ("diffuse a", (1, 1, 1)),
    ("diffuse a_alpha", (1, 1, 1)),
    ("diffuse b_alpha", (1, 1, 1)),
    ("diffuse b", (1, 1, 1)),
    ("diffusecolor", (1, 1, 1)),
    ("layer a tint", (1, 1, 1)),
    ("layer b tint", (1, 1, 1)),
    ("tint", (1, 1, 1)),
    ("mra", (0, 0.5, 1)),
    ("mra a", (0, 0.5, 1)),
    ("mra b", (0, 0.5, 1)),
    ("normal", (0, 0, 1)),
    ("metallic", (1, 1, 1)),
    ("metallic b", (0, 0, 0)),
    ("roughness max", (0.75, 0.75, 0.75)),
    ("roughness min", (0.1, 0.1, 0.1)),
    ("roughness mult", (1, 1, 1)),
    ("roughness a max", (0.75, 0.75, 0.75)),
    ("roughness a min", (0.1, 0.1, 0.1)),
    ("roughness a mult", (1, 1, 1)),
    ("roughness b max", (0.75, 0.75, 0.75)),
    ("roughness b min", (0.1, 0.1, 0.1)),
    ("roughness b mult", (1, 1, 1)),
    ("blend roughness", (1, 1, 1)),
    ("blend to flat mra", (0, 0, 0)),
    ("use alpha as emissive", (0, 0, 0)),
    ("emissive mult", (0, 0, 0)),
    ("specular", (0.17, 0.17, 0.17)),
    ("use vertex color", (1, 1, 1)),
    ("blend tint only", (0, 0, 0)),
    ("use diffuse b alpha", (0, 0, 0)),
    ("blend to flat", (0, 0, 0)),
    ("invert alpha (texture)", (0, 0, 0)),
    ("invert vertex alpha (vertex color)", (0, 0, 0)),
    ("use vertex alpha", (1, 1, 1)),
    ("use 2 diffuse maps", (1, 1, 1)),
    ("mask multiply", (1, 1, 1)),
    ("mask blend mult", (1, 1, 1)),
    ("mask blend power", (0.1, 0.1, 0.1)),
    ("normal mask blend mult", (1, 1, 1)),
    ("normal mask blend power", (0.1, 0.1, 0.1))
    ]
    for name, value in default_params:
        if name in N_SHADER.inputs and N_SHADER.inputs[name].is_linked is False:
            set_default(name, value)
  
def get_image(tex_name, tex_local_path):
    img = bpy.data.images.get(tex_name + ".png")
    if img is None:
        img = bpy.data.images.load(tex_local_path)
    return img

    # if "CachedReferencedTextures" in mat_props:
    #     pos = [-1300, 0]
    #     if override:
    #         pos = [-1300, 0]
    #     i = 0
    #     textures = mat_props["CachedReferencedTextures"]
    #     for index, param, in enumerate(textures):
    #         if param is not None:

    #             texture_name_raw = param["ObjectName"].replace("Texture2D ", "")
    #             if texture_name_raw not in blacklist_tex:
    #                 texture_path_raw = param["ObjectPath"]

    #                 tex_game_path = get_texture_path_yo(s=texture_path_raw, f=settings.texture_format)
    #                 tex_local_path = settings.assets_path.joinpath(tex_game_path).__str__()

    #                 if Path(tex_local_path).exists():
    #                     pos[1] = i * -270
    #                     i += 1
    #                     tex_image_node = mat.node_tree.nodes.new('OctaneRGBImage')
    #                     tex_image_node.image = get_image(Path(tex_local_path).stem, tex_local_path)  # bpy.data.images.load(tex_local_path)
    #                     tex_image_node.image.alpha_mode = "CHANNEL_PACKED"
    #                     tex_image_node.label = texture_name_raw
    #                     tex_image_node.location = [pos[0], pos[1]]

    #                     if shader.node_tree == get_valorant_shader(group_name="VALORANT_Ventsmoke"):
    #                         if texture_name_raw == "SmokeGradient_TFX":
    #                             mat.node_tree.links.new(tex_image_node.outputs["Color"], shader.inputs["Smoke_Gradient"])
    #                             tex_image_node.image.colorspace_settings.name = "Non-Color"

    #                         if texture_name_raw == "VentSmoke_Mask":
    #                             mat.node_tree.links.new(mapping.outputs["Mapping"], tex_image_node.inputs["Vector"])
    #                             mat.node_tree.links.new(tex_image_node.outputs["Color"], shader.inputs["Ventsmoke"])
    #                             tex_image_node.image.colorspace_settings.name = "Non-Color"

    #                     if shader.node_tree == get_valorant_shader(group_name="VALORANT_Waterfall"):
    #                         if texture_name_raw == "Waterfall_Disolve_Blur_TFX":
    #                             mat.node_tree.links.new(mapping.outputs["UV"], tex_image_node.inputs["Vector"])
    #                             mat.node_tree.links.new(tex_image_node.outputs["Color"], shader.inputs["Waterfall_Disolve_Blur"])

    #                         elif texture_name_raw == "Waterfall_Wave_TFX":
    #                             mat.node_tree.links.new(mapping.outputs["UV"], tex_image_node.inputs["Vector"])
    #                             mat.node_tree.links.new(tex_image_node.outputs["Color"], shader.inputs["Waterfall_Wave"])

    #                         elif texture_name_raw == "Waterfall_BaseMask_TFX":
    #                             mat.node_tree.links.new(mapping.outputs["UV"], tex_image_node.inputs["Vector"])
    #                             mat.node_tree.links.new(tex_image_node.outputs["Color"], shader.inputs["Waterfall_BaseMask"])

    #                         elif texture_name_raw == "Waterfall_Ripples_TFX":
    #                             mat.node_tree.links.new(mapping.outputs["Vector"], tex_image_node.inputs["Vector"])
    #                             mat.node_tree.links.new(tex_image_node.outputs["Color"], shader.inputs["Waterfall_Ripples"])
    #                             tex_image_node.extension = "EXTEND"

    #                     if texture_name_raw == "GlowA01_DIFF":
    #                         if "Alpha" in shader.inputs:
    #                             mat.node_tree.links.new(tex_image_node.outputs["Color"], shader.inputs["Alpha"])
    #                             tex_image_node.extension = "EXTEND"

    #                     if texture_name_raw == "GradientVertB_TEX":
    #                         if "Gradient_Cache" in shader.inputs:
    #                             mat.node_tree.links.new(tex_image_node.outputs["Color"], shader.inputs["Gradient_Cache"])
    #                             tex_image_node.extension = "EXTEND"

    #                     if "_DF" in texture_name_raw:
    #                         nodes_texture["diffuse"] = tex_image_node

    #                     else:
    #                         nodes_texture[texture_name_raw] = tex_image_node

    #                     TextureParameterValues.append(texture_name_raw.lower())

    # elif "CachedExpressionData"in mat_props:
    #     pos = [-1300, 0]
    #     i = 0
    #     if "ReferencedTextures" in mat_props["CachedExpressionData"]:
    #         textures = mat_props["CachedExpressionData"]["ReferencedTextures"] 
    #         for index, param, in enumerate(textures):
    #             if param is not None:

    #                 texture_name_raw = param["ObjectName"].replace("Texture2D ", "")
    #                 if texture_name_raw not in blacklist_tex:
    #                     texture_path_raw = param["ObjectPath"]

    #                     tex_game_path = get_texture_path_yo(s=texture_path_raw, f=settings.texture_format)
    #                     tex_local_path = settings.assets_path.joinpath(tex_game_path).__str__()

    #                     if Path(tex_local_path).exists():
    #                         pos[1] = i * -270
    #                         i += 1
    #                         tex_image_node = mat.node_tree.nodes.new('OctaneRGBImage')
    #                         tex_image_node.image = get_image(Path(tex_local_path).stem, tex_local_path)
    #                         tex_image_node.image.alpha_mode = "CHANNEL_PACKED"
    #                         tex_image_node.label = texture_name_raw
    #                         tex_image_node.location = [pos[0], pos[1]]

    #                         if "_mk" in texture_name_raw:
    #                             if "MRA" in shader.inputs:
    #                                 mat.node_tree.links.new(tex_image_node.outputs["Color"], shader.inputs["MRA"])
    #                                 shader.inputs["Metallic"].default_value = -1
    #                                 shader.inputs["Roughness"].default_value = -1
    #                                 shader.inputs["AO Strength"].default_value = 0.15

    #                         if "_DF" in texture_name_raw:
    #                             if "DF" in shader.inputs:
    #                                 mat.node_tree.links.new(tex_image_node.outputs["Color"], shader.inputs["DF"])
    #                                 mat.node_tree.links.new(tex_image_node.outputs["Alpha"], shader.inputs["Alpha"])
    #                                 mat.node_tree.links.new(tex_image_node.outputs["Alpha"], shader.inputs["DF Alpha"])

    #                         if "_NM" in texture_name_raw:
    #                             if "NM" in shader.inputs:
    #                                 mat.node_tree.links.new(tex_image_node.outputs["Color"], shader.inputs["NM"])

    #                         if "_MRA" in texture_name_raw:
    #                             if "MRA" in shader.inputs:
    #                                 mat.node_tree.links.new(tex_image_node.outputs["Color"], shader.inputs["MRA"])

                            # if "T_CGSkies_0091_ascent_DF" in texture_name_raw:
                            #     if "Light" in shader.inputs:
                            #         mat.node_tree.links.new(tex_image_node.outputs["Color"], shader.inputs["Light"])

                            #         world_nodes = bpy.context.scene.world.node_tree.nodes
                            #         world_nodes.clear()

                            #         node_background = world_nodes.new(type='ShaderNodeBackground')
                            #         node_output = world_nodes.new(type='ShaderNodeOutputWorld')   
                            #         node_output.location = 200,0

                            #         node_environment = world_nodes.new('ShaderNodeTexEnvironment')
                            #         node_environment.image = bpy.data.images.load(tex_local_path)
                            #         node_environment.label = texture_name_raw
                            #         node_environment.location = -300,0
                        
                            #         links = bpy.context.scene.world.node_tree.links
                            #         links.new(node_environment.outputs["Color"], node_background.inputs["Color"])
                            #         links.new(node_background.outputs["Background"], node_output.inputs["Surface"])

                            # if "Skybox" in texture_name_raw:
                            #     if "Background" in shader.inputs:
                            #         mat.node_tree.links.new(tex_image_node.outputs["Color"], shader.inputs["Background"])

    #return nodes_texture
# !SECTION


# ANCHOR : IMPORTERS

def filter_objects(umap_DATA, lights: bool = False) -> list:

    objects = umap_DATA
    filtered_list = []

    # Debug check
    if SELECTIVE_OBJECTS:
        for filter_model_name in SELECTIVE_OBJECTS:
            for og_model in objects:
                object_type = get_object_type(og_model)
                if object_type == "mesh":
                    if filter_model_name in og_model["Properties"]["StaticMesh"]["ObjectPath"]:
                        og_model["Name"] = og_model["Properties"]["StaticMesh"]["ObjectPath"]
                        filtered_list.append(og_model)

                elif object_type == "decal":
                    if filter_model_name in og_model["Outer"]:
                        og_model["Name"] = og_model["Outer"]
                        filtered_list.append(og_model)

                elif object_type == "light":
                    if filter_model_name in og_model["Outer"]:
                        og_model["Name"] = og_model["Outer"]
                        filtered_list.append(og_model)

    else:
        filtered_list = objects

    new_list = []

    def is_blacklisted(object_name: str) -> bool:
        for blocked in BLACKLIST:
            if blocked.lower() in object_name.lower():
                return True
        return False

    # Check for blacklisted items
    for og_model in filtered_list:
        model_name_lower = get_object_name(data=og_model, mat=False).lower()
        if "OverrideMaterials" in og_model["Properties"]:
            if og_model["Properties"]["OverrideMaterials"][0]:
                mat_name_lower = og_model["Properties"]["OverrideMaterials"][0]["ObjectName"]
            else:
                mat_name_lower = "none"
        else:
            mat_name_lower = "none"

        if is_blacklisted(model_name_lower):
            continue
        if is_blacklisted(mat_name_lower):
            continue
        else:
            new_list.append(og_model)

    return new_list


def import_umap(settings: Settings, umap_data: dict, umap_name: str):
    logger.info(f"Processing : {umap_name}")
    # main_scene = bpy.data.scenes["Scene"]


    main_scene = bpy.data.scenes["Scene"]
    map_collection = bpy.data.collections.new(settings.selected_map.name.capitalize())
    main_scene.collection.children.link(map_collection)

    import_collection = bpy.data.collections.new(umap_name)
    map_collection.children.link(import_collection)

    objectsToImport = filter_objects(umap_data)
    decals_collection = bpy.data.collections.new(umap_name + "_Decals")
    lights_collection = bpy.data.collections.new(umap_name + "_Lights")

    import_collection.children.link(decals_collection)
    import_collection.children.link(lights_collection)

    # import_collection.children.link(objects_collection)

    if COUNT != 0:
        objectsToImport = objectsToImport[:COUNT]

    for objectIndex, object_data in enumerate(objectsToImport):
        objectIndex = f"{objectIndex:03}"
        object_type = get_object_type(object_data)

        if object_type == "mesh":
            if "EMPTY" not in umap_name:
                pass

                map_object = MapObject(settings=settings, data=object_data, umap_name=umap_name)
                imported_object = import_object(map_object=map_object, target_collection=import_collection, object_index=objectIndex)
                set_materials(settings=settings, byo=imported_object, map_object=map_object)

        if object_type == "decal" and settings.import_decals:

            if "DecalSize" in object_data["Properties"]:
                size = object_data["Properties"]["DecalSize"]
                decal_size = (size["X"] * 0.01, size["Y"] * 0.01, size["Z"] * 0.01)
            else:
                decal_size = (1, 1, 1)
            bpy.ops.mesh.primitive_cube_add(size=2, enter_editmode=False, align='WORLD', location=(0, 0, 0), scale=decal_size)
            decal_object = bpy.context.active_object
            decal_object.name = object_data["Outer"]
            set_properties(byo=decal_object, object=object_data["Properties"], is_instanced=False)

            set_materials(settings=settings, byo=decal_object, map_object=object_data, decal=True)

            decals_collection.objects.link(decal_object)
            main_scene.collection.objects.unlink(decal_object)

        if object_type == "light" and settings.import_lights:
            # Set variables
            light_type = get_light_type(object_data)
            light_name = object_data["Outer"]
            light_props = object_data["Properties"]
            
            light_intensity = 0
            if "Intensity" in object_data["Properties"]:
                light_intensity = object_data["Properties"]["Intensity"]

            logger.info(f"[{objectIndex}] | Lighting : {light_name}")

            light_data = bpy.data.lights.new(name=light_name, type=light_type)
            light_object = bpy.data.objects.new(name=light_name, object_data=light_data)
            lights_collection.objects.link(light_object)

            for prop_name, prop_value in light_props.items():
                OtherTypes.append(prop_name)
                if "Intensity" == prop_name:
                    if light_type == "POINT":    
                        if "IntensityUnits" in object_data["Properties"]:
                            light_object.data.energy = light_intensity / (4 * pi) / 683
                        else:
                            light_object.data.energy = light_intensity * 49.7 / 683
                    elif light_type == "AREA":
                        if "IntensityUnits" in object_data["Properties"]:
                            light_object.data.energy = light_intensity / (2 * pi) / 683
                        else:
                            light_object.data.energy = light_intensity * 199 / 683
                    elif light_type == "SPOT":
                        if "IntensityUnits" in object_data["Properties"]:
                            light_object.data.energy = light_intensity / (4 * pi) / 683
                        else:
                            light_object.data.energy = light_intensity * 49.7 / 683
                    elif light_type == "SUN":
                        light_object.data.energy = light_intensity * 350 / 683 #random multiplier because unreal lux is wrong
                elif "LightColor" == prop_name:
                    light_object.data.color = get_rgb_255(prop_value)
                elif "SourceRadius" == prop_name:
                    if light_type == "SPOT":
                        light_object.data.shadow_soft_size = prop_value * 0.01
                    else:
                        light_object.data.shadow_soft_size = prop_value * 0.1

                if light_type == "AREA":
                    light_object.data.shape = 'RECTANGLE'
                    if "SourceWidth" == prop_name:
                        light_object.data.size = prop_value * 0.01
                    elif "SourceHeight" == prop_name:
                        light_object.data.size_y = prop_value * 0.01

                elif light_type == "SPOT":
                    light_object.data.spot_blend = 1
                    if "OuterConeAngle" == prop_name:
                        light_object.data.spot_size = radians(prop_value)

            set_properties(byo=light_object, object=light_props, is_light=True)

    if len(decals_collection.objects) <= 0:
        bpy.data.collections.remove(decals_collection)
    if len(lights_collection.objects) <= 0:
        bpy.data.collections.remove(lights_collection)
    # if len(import_collection.objects) <= 0:
    #     bpy.data.collections.remove(import_collection)

    if not settings.debug:
        with redirect_stdout(stdout):

            if settings.textures == "pack":
                bpy.ops.file.pack_all()

            if settings.textures == "local":
                bpy.ops.file.pack_all()
                bpy.ops.file.unpack_all(method='WRITE_LOCAL')
                bpy.ops.file.make_paths_relative()
                logger.info(f"Extracted : {umap_name}'s textures to {shorten_path(settings.selected_map.scenes_path.joinpath('textures').__str__(), 4)}")

            map_path = settings.selected_map.scenes_path.joinpath(umap_name).__str__()
            bpy.ops.wm.save_as_mainfile(filepath=map_path + ".blend", compress=True)
            logger.info(f"Saved : {umap_name}.blend to {shorten_path(map_path.__str__(), 4)}")


def import_object(map_object: MapObject, target_collection: bpy.types.Collection, object_index: int):
    scene = bpy.data.scenes["Scene"]

    link = target_collection.objects.link
    scene_unlink = scene.collection.objects.unlink
    collection_unlink = target_collection.objects.unlink
    master_object = None

    if Path(map_object.model_path).exists():

        master_object: bpy.types.Object
        master_object = get_object(map_object, object_index, link, scene_unlink)

        if "LODData" in map_object.data:
            lod_data = map_object.data["LODData"][0]
            # Vertex colors
            if "OverrideVertexColors" in lod_data:
                if "Data" in lod_data["OverrideVertexColors"]:
                    vertex_colors_hex = lod_data["OverrideVertexColors"]["Data"]

                    mo: Mesh = master_object.data

                    vertex_colors = [
                        [
                            x / 255
                            for x in unpack_4uint8(bytes.fromhex(rgba_hex))
                        ]
                        for rgba_hex in vertex_colors_hex
                    ]

                    set_vcols_on_layer(mo, vertex_colors)

        # Let's goooooooo!
        if map_object.is_instanced():

            instance_data = map_object.data["PerInstanceSMData"]

            # bpy.ops.object.empty_add(type='PLAIN_AXES')
            # instance_group = bpy.context.active_object
            instance_group = bpy.data.objects.new(map_object.name + "-GRP", None)
            # instance_group.name = map_object.name + "-GRP"

            link(instance_group)
            # scene_unlink(instance_group)

            master_object.parent = instance_group

            # move_collection(instanced_collection, instance_group, scene)
            reset_properties(instance_group)
            set_properties(byo=instance_group, object=map_object.data["Properties"], is_instanced=False)

            master_object.hide_viewport = True
            master_object.hide_render = True

            for index, instance_data in enumerate(instance_data):
                instance_object = master_object.copy()
                instance_object.hide_viewport = False
                instance_object.hide_render = False
                link(instance_object)

                set_properties(instance_object, instance_data, is_instanced=True)
                logger.info(f"[{object_index}] | Instancing : {shorten_path(map_object.model_path, 4)}")

            master_object.hide_viewport = True
            master_object.hide_render = True

        else:
            master_object.hide_viewport = False
            master_object.hide_render = False

        set_properties(byo=master_object, object=map_object.data["Properties"], is_instanced=False)

    return master_object


# ANCHOR Post Processing

def combine_umaps(settings: Settings):

    # ! Import other .blend files back!
    # a = SELECTIVE_UMAP or settings.selected_map.umaps
    # print(settings.selected_map)

    for umap in settings.selected_map.umaps:
        umap_name = os.path.splitext(os.path.basename(umap))[0]
        umap_blend_file = settings.selected_map.scenes_path.joinpath(umap_name).__str__() + ".blend"

        # logger.info(settings.combine_method)
        sec = "\\Collection\\"
        obj = umap_name

        fp = umap_blend_file + sec + obj
        dr = umap_blend_file + sec

        if Path(umap_blend_file).exists():

            if settings.combine_method == "append":
                bpy.ops.wm.append(filepath=fp, filename=obj, directory=dr)
            if settings.combine_method == "link":
                bpy.ops.wm.link(filepath=fp, filename=obj, directory=dr)


def post_setup(settings: Settings):

    # ! Save umap to .blend file
    if settings.combine_umaps:
        with redirect_stdout(stdout):
            logger.info(f"Combining : {settings.selected_map.name.capitalize()}'s parts to a single blend file...")
            map_path = settings.selected_map.scenes_path.joinpath(settings.selected_map.name.capitalize()).__str__()
            bpy.ops.wm.save_as_mainfile(filepath=map_path + ".blend", compress=True)

            # ! Clear everything
            clean_scene(debug=settings.debug)

            combine_umaps(settings=settings)

            # eliminate_materials()
            remove_duplicate_mats()
            clear_duplicate_node_groups()

            # ! Utility to pack
            if settings.textures == "pack":
                bpy.ops.file.pack_all()
            if settings.textures == "local":
                bpy.ops.file.unpack_all(method='WRITE_LOCAL')
                logger.info("Unpacked local textures")

            bpy.ops.wm.save_as_mainfile(filepath=map_path + ".blend", compress=True)
            logger.info(f"Saved Combined : '{settings.selected_map.name.capitalize()}.blend' to {shorten_path(map_path, 4)}")


# ANCHOR MAIN FUNCTION

def import_map(addon_prefs):
    """
    Main function
    Args:
        settings (dict): Settings to use
    """

    os.system("cls")
    settings = Settings(addon_prefs)

    if (not addon_prefs.isInjected) and addon_prefs.usePerfPatch:
        inject_dll(os.getpid(), settings.dll_path.__str__())
        addon_prefs.isInjected = True
    

    # Clear the scene
    clean_scene()

    # Import the shaders
    import_shaders(settings)
    clear_duplicate_node_groups()

    umap_json_paths = get_map_assets(settings)

    if SELECTIVE_UMAP:
        settings.selected_map.umaps = SELECTIVE_UMAP
        umap_json_paths = []
        for umap in SELECTIVE_UMAP:
            umap_json_paths.append(settings.selected_map.umaps_path.joinpath(f"{umap}.json"))


    # Process each umaps
    umap_json_path: Path
    for umap_json_path in umap_json_paths:

        if not settings.debug:
            clean_scene(debug=settings.debug)

        umap_data = read_json(umap_json_path)
        umap_name = umap_json_path.stem

        import_umap(settings=settings, umap_data=umap_data, umap_name=umap_name)
        remove_master_objects()
        clear_duplicate_node_groups()
    
    

    # Final
    if settings.debug:
        PROPS = {

            "ScalarParameterValues": list(dict.fromkeys(ScalarParameterValues)),
            "StaticParameterValues": list(dict.fromkeys(StaticParameterValues)),
            "TextureParameterValues": list(dict.fromkeys(TextureParameterValues)),
            "BasePropertyOverrides": BasePropertyOverrides,
            "VectorParameterValues": list(dict.fromkeys(VectorParameterValues)),
            "MaterialTypes": list(dict.fromkeys(MaterialTypes)),
            "OtherTypes": list(dict.fromkeys(OtherTypes))
        }

        save_json(settings.selected_map.folder_path.joinpath("props.json"), PROPS)
        save_json(settings.selected_map.folder_path.joinpath("MaterialTypes.json"), list(dict.fromkeys(MaterialTypes)))
        save_json(settings.selected_map.folder_path.joinpath("object_types.json"), list(dict.fromkeys(flatten_list(object_types))))

    else:
        post_setup(settings)
        open_folder(settings.selected_map.scenes_path.__str__())

    logger.info("Finished!")
