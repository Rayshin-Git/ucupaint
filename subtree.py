import bpy, re
from . import lib, Modifier, MaskModifier
from .common import *
from .node_arrangements import *
from .node_connections import *

def create_input(tree, name, socket_type, valid_inputs, index, 
        dirty = False, min_value=None, max_value=None, default_value=None):

    inp = tree.inputs.get(name)
    if not inp:
        inp = tree.inputs.new(socket_type, name)
        if min_value != None: inp.min_value = min_value
        if max_value != None: inp.max_value = max_value
        if default_value != None: inp.default_value = default_value
        dirty = True
    valid_inputs.append(inp)
    fix_io_index(inp, tree.inputs, index)

    return dirty

def create_output(tree, name, socket_type, valid_outputs, index, dirty=False):

    outp = tree.outputs.get(name)
    if not outp:
        outp = tree.outputs.new(socket_type, name)
        dirty = True
    valid_outputs.append(outp)
    fix_io_index(outp, tree.outputs, index)

    return dirty

def check_layer_tree_ios(layer, tree=None):

    yp = layer.id_data.yp
    if not tree: tree = get_tree(layer)

    dirty = False

    input_index = 0
    output_index = 0
    valid_inputs = []
    valid_outputs = []

    has_parent = layer.parent_idx != -1
    
    # Tree input and outputs
    for i, ch in enumerate(layer.channels):
        #if yp.disable_quick_toggle and not ch.enable: continue
        if not ch.enable: continue

        root_ch = yp.channels[i]
        dirty = create_input(tree, root_ch.name, channel_socket_input_bl_idnames[root_ch.type], 
                valid_inputs, input_index, dirty)
        dirty = create_output(tree, root_ch.name, channel_socket_output_bl_idnames[root_ch.type], 
                valid_outputs, output_index, dirty)
        input_index += 1
        output_index += 1

        # Alpha IO
        if (root_ch.type == 'RGB' and root_ch.enable_alpha) or has_parent:

            name = root_ch.name + io_suffix['ALPHA']
            dirty = create_input(tree, name, 'NodeSocketFloatFactor', valid_inputs, input_index, dirty)
            dirty = create_output(tree, name, 'NodeSocketFloat', valid_outputs, output_index, dirty)
            input_index += 1
            output_index += 1

        # Displacement IO
        if root_ch.type == 'NORMAL': # and root_ch.enable_parallax:

            if not root_ch.enable_smooth_bump:

                name = root_ch.name + io_suffix['HEIGHT']
                dirty = create_input(tree, name, 'NodeSocketFloatFactor', valid_inputs, input_index, dirty)
                dirty = create_output(tree, name, 'NodeSocketFloat', valid_outputs, output_index, dirty)
                input_index += 1
                output_index += 1

                if has_parent:

                    name = root_ch.name + io_suffix['HEIGHT'] + io_suffix['ALPHA']
                    dirty = create_input(tree, name, 'NodeSocketFloatFactor', valid_inputs, input_index, dirty)
                    dirty = create_output(tree, name, 'NodeSocketFloat', valid_outputs, output_index, dirty)
                    input_index += 1
                    output_index += 1

            else:

                name = root_ch.name + io_suffix['HEIGHT_ONS']
                dirty = create_input(tree, name, 'NodeSocketVector', valid_inputs, input_index, dirty)
                dirty = create_output(tree, name, 'NodeSocketVector', valid_outputs, output_index, dirty)
                input_index += 1
                output_index += 1

                name = root_ch.name + io_suffix['HEIGHT_EW']
                dirty = create_input(tree, name, 'NodeSocketVector', valid_inputs, input_index, dirty)
                dirty = create_output(tree, name, 'NodeSocketVector', valid_outputs, output_index, dirty)
                input_index += 1
                output_index += 1

                if has_parent:

                    name = root_ch.name + io_suffix['HEIGHT_ONS'] + io_suffix['ALPHA']
                    dirty = create_input(tree, name, 'NodeSocketVector', valid_inputs, input_index, dirty)
                    dirty = create_output(tree, name, 'NodeSocketVector', valid_outputs, output_index, dirty)
                    input_index += 1
                    output_index += 1

                    name = root_ch.name + io_suffix['HEIGHT_EW'] + io_suffix['ALPHA']
                    dirty = create_input(tree, name, 'NodeSocketVector', valid_inputs, input_index, dirty)
                    dirty = create_output(tree, name, 'NodeSocketVector', valid_outputs, output_index, dirty)
                    input_index += 1
                    output_index += 1

                #for d in neighbor_directions:

                #    name = root_ch.name + io_suffix['HEIGHT'] + ' ' + d
                #    dirty = create_input(tree, name, 'NodeSocketFloatFactor', valid_inputs, input_index, dirty)
                #    dirty = create_output(tree, name, 'NodeSocketFloat', valid_outputs, output_index, dirty)
                #    input_index += 1
                #    output_index += 1

                #    if has_parent:

                #        name = root_ch.name + io_suffix['ALPHA'] + ' ' + d
                #        dirty = create_input(tree, name, 'NodeSocketFloatFactor', valid_inputs, input_index, dirty)
                #        dirty = create_output(tree, name, 'NodeSocketFloat', valid_outputs, output_index, dirty)
                #        input_index += 1
                #        output_index += 1

    # Tree background inputs
    if layer.type in {'BACKGROUND', 'GROUP'}:

        for i, ch in enumerate(layer.channels):
            #if yp.disable_quick_toggle and not ch.enable: continue
            if not ch.enable: continue

            root_ch = yp.channels[i]

            name = root_ch.name + io_suffix[layer.type]
            dirty = create_input(tree, name, channel_socket_input_bl_idnames[root_ch.type],
                    valid_inputs, input_index, dirty)
            input_index += 1

            # Alpha Input
            if root_ch.enable_alpha or layer.type == 'GROUP':

                name = root_ch.name + io_suffix['ALPHA'] + io_suffix[layer.type]
                dirty = create_input(tree, name, 'NodeSocketFloatFactor',
                        valid_inputs, input_index, dirty)
                input_index += 1

            # Displacement Input
            if root_ch.type == 'NORMAL' and layer.type == 'GROUP':

                if not root_ch.enable_smooth_bump:

                    name = root_ch.name + io_suffix['HEIGHT'] + io_suffix['GROUP']
                    dirty = create_input(tree, name, 'NodeSocketFloat',
                            valid_inputs, input_index, dirty)
                    input_index += 1

                    name = root_ch.name + io_suffix['HEIGHT'] + io_suffix['ALPHA'] + io_suffix['GROUP']
                    dirty = create_input(tree, name, 'NodeSocketFloat',
                            valid_inputs, input_index, dirty)
                    input_index += 1

                else:

                    name = root_ch.name + io_suffix['HEIGHT_ONS'] + io_suffix['GROUP']
                    dirty = create_input(tree, name, 'NodeSocketVector', valid_inputs, input_index, dirty)
                    input_index += 1

                    name = root_ch.name + io_suffix['HEIGHT_EW'] + io_suffix['GROUP']
                    dirty = create_input(tree, name, 'NodeSocketVector', valid_inputs, input_index, dirty)
                    input_index += 1

                    name = root_ch.name + io_suffix['HEIGHT_ONS'] + io_suffix['ALPHA'] + io_suffix['GROUP']
                    dirty = create_input(tree, name, 'NodeSocketVector', valid_inputs, input_index, dirty)
                    input_index += 1

                    name = root_ch.name + io_suffix['HEIGHT_EW'] + io_suffix['ALPHA'] + io_suffix['GROUP']
                    dirty = create_input(tree, name, 'NodeSocketVector', valid_inputs, input_index, dirty)
                    input_index += 1

                    #for d in neighbor_directions:
                    #    name = root_ch.name + io_suffix['HEIGHT'] + ' ' + d + io_suffix['GROUP']

                    #    dirty = create_input(tree, name, 'NodeSocketFloat', valid_inputs, input_index, dirty)
                    #    input_index += 1

                    #    name = (root_ch.name + 
                    #            #io_suffix['HEIGHT'] + ' ' + 
                    #            io_suffix['ALPHA'] + ' ' + 
                    #            d + io_suffix['GROUP'])

                    #    dirty = create_input(tree, name, 'NodeSocketFloatFactor', valid_inputs, input_index, dirty)
                    #    input_index += 1

    # UV necessary container
    uv_names = []

    # Check height root channel
    height_root_ch = get_root_height_channel(yp)
    height_ch = get_height_channel(layer)
    if height_root_ch and height_root_ch.main_uv != '' and height_root_ch.main_uv not in uv_names:
        uv_names.append(height_root_ch.main_uv)

    # Check layer uv
    if layer.texcoord_type == 'UV' and layer.uv_name not in uv_names:
        uv_names.append(layer.uv_name)

    # Check masks uvs
    for mask in layer.masks:
        if mask.texcoord_type == 'UV' and mask.uv_name not in uv_names:
            uv_names.append(mask.uv_name)

    # Create inputs
    for uv_name in uv_names:
        name = uv_name + io_suffix['UV']
        dirty = create_input(tree, name, 'NodeSocketVector', valid_inputs, input_index, dirty)
        input_index += 1

        #if height_ch and not (yp.disable_quick_toggle and not height_ch.enable):
        if height_ch and height_ch.enable:

            name = uv_name + io_suffix['TANGENT']
            dirty = create_input(tree, name, 'NodeSocketVector', valid_inputs, input_index, dirty)
            input_index += 1

            name = uv_name + io_suffix['BITANGENT']
            dirty = create_input(tree, name, 'NodeSocketVector', valid_inputs, input_index, dirty)
            input_index += 1

    # Other than uv texcoord name container
    texcoords = []

    # Check layer
    if layer.texcoord_type != 'UV':
        texcoords.append(layer.texcoord_type)

    for mask in layer.masks:
        if mask.texcoord_type != 'UV' and mask.texcoord_type not in texcoords:
            texcoords.append(mask.texcoord_type)

    for texcoord in texcoords:
        name = io_names[texcoord]
        dirty = create_input(tree, name, 'NodeSocketVector', valid_inputs, input_index, dirty)
        input_index += 1

    # Check for invalid io
    for inp in tree.inputs:
        if inp not in valid_inputs:
            tree.inputs.remove(inp)

    for outp in tree.outputs:
        if outp not in valid_outputs:
            tree.outputs.remove(outp)

    return dirty

def move_mod_group(layer, from_tree, to_tree):
    mod_group = from_tree.nodes.get(layer.mod_group)
    if mod_group:
        mod_tree = mod_group.node_tree
        remove_node(from_tree, layer, 'mod_group', remove_data=False)
        remove_node(from_tree, layer, 'mod_group_1', remove_data=False)

        mod_group = new_node(to_tree, layer, 'mod_group', 'ShaderNodeGroup', 'mod_group')
        mod_group.node_tree = mod_tree
        mod_group_1 = new_node(to_tree, layer, 'mod_group_1', 'ShaderNodeGroup', 'mod_group_1')
        mod_group_1.node_tree = mod_tree

def refresh_source_tree_ios(source_tree, layer_type):

    # Create input and outputs
    inp = source_tree.inputs.get('Vector')
    if not inp: source_tree.inputs.new('NodeSocketVector', 'Vector')

    out = source_tree.outputs.get('Color')
    if not out: source_tree.outputs.new('NodeSocketColor', 'Color')

    out = source_tree.outputs.get('Alpha')
    if not out: source_tree.outputs.new('NodeSocketFloat', 'Alpha')

    col1 = source_tree.outputs.get('Color 1')
    alp1 = source_tree.outputs.get('Alpha 1')
    #solid = source_tree.nodes.get(ONE_VALUE)

    if layer_type != 'IMAGE':

        if not col1: col1 = source_tree.outputs.new('NodeSocketColor', 'Color 1')
        if not alp1: alp1 = source_tree.outputs.new('NodeSocketFloat', 'Alpha 1')

        #if not solid:
        #    solid = source_tree.nodes.new('ShaderNodeValue')
        #    solid.outputs[0].default_value = 1.0
        #    solid.name = ONE_VALUE
    else:
        if col1: source_tree.outputs.remove(col1)
        if alp1: source_tree.outputs.remove(alp1)
        #if solid: source_tree.nodes.remove(solid)

def enable_layer_source_tree(layer, rearrange=False):

    # Check if source tree is already available
    #if layer.type in {'BACKGROUND', 'COLOR', 'GROUP'}: return
    if layer.type in {'BACKGROUND', 'COLOR'}: return
    if layer.type != 'VCOL' and layer.source_group != '': return

    layer_tree = get_tree(layer)

    if layer.type not in {'VCOL', 'GROUP'}:
        # Get current source for reference
        source_ref = layer_tree.nodes.get(layer.source)
        mapping_ref = layer_tree.nodes.get(layer.mapping)

        # Create source tree
        source_tree = bpy.data.node_groups.new(LAYERGROUP_PREFIX + layer.name + ' Source', 'ShaderNodeTree')

        #source_tree.outputs.new('NodeSocketFloat', 'Factor')

        create_essential_nodes(source_tree, True)

        refresh_source_tree_ios(source_tree, layer.type)

        # Copy source from reference
        source = new_node(source_tree, layer, 'source', source_ref.bl_idname)
        copy_node_props(source_ref, source)

        mapping = new_node(source_tree, layer, 'mapping', 'ShaderNodeMapping')
        if mapping_ref: copy_node_props(mapping_ref, mapping)

        # Create source node group
        source_group = new_node(layer_tree, layer, 'source_group', 'ShaderNodeGroup', 'source_group')
        source_n = new_node(layer_tree, layer, 'source_n', 'ShaderNodeGroup', 'source_n')
        source_s = new_node(layer_tree, layer, 'source_s', 'ShaderNodeGroup', 'source_s')
        source_e = new_node(layer_tree, layer, 'source_e', 'ShaderNodeGroup', 'source_e')
        source_w = new_node(layer_tree, layer, 'source_w', 'ShaderNodeGroup', 'source_w')

        source_group.node_tree = source_tree
        source_n.node_tree = source_tree
        source_s.node_tree = source_tree
        source_e.node_tree = source_tree
        source_w.node_tree = source_tree

        # Remove previous source
        layer_tree.nodes.remove(source_ref)
        if mapping_ref: layer_tree.nodes.remove(mapping_ref)
    
        # Bring modifiers to source tree
        if layer.type == 'IMAGE':
            for mod in layer.modifiers:
                Modifier.add_modifier_nodes(mod, source_tree, layer_tree)
        else:
            move_mod_group(layer, layer_tree, source_tree)

    # Create uv neighbor
    #if layer.type in {'VCOL', 'GROUP'}:
    if layer.type in {'VCOL'}:
        uv_neighbor = replace_new_node(layer_tree, layer, 'uv_neighbor', 'ShaderNodeGroup', 'Neighbor UV', 
                lib.NEIGHBOR_FAKE, hard_replace=True)
    #else: 
    elif layer.type != 'GROUP': 
        uv_neighbor = replace_new_node(layer_tree, layer, 'uv_neighbor', 'ShaderNodeGroup', 'Neighbor UV', 
                lib.get_neighbor_uv_tree_name(layer.texcoord_type, entity=layer), hard_replace=True)
        set_uv_neighbor_resolution(layer, uv_neighbor)

    if rearrange:
        # Reconnect outside nodes
        reconnect_layer_nodes(layer)

        # Rearrange nodes
        rearrange_layer_nodes(layer)

def disable_layer_source_tree(layer, rearrange=True):

    yp = layer.id_data.yp

    # Check if fine bump map is used on some of layer channels
    smooth_bump_ch = None
    for i, root_ch in enumerate(yp.channels):
        if root_ch.type == 'NORMAL' and root_ch.enable_smooth_bump and layer.channels[i].enable:
            smooth_bump_ch = root_ch

    if (layer.type != 'VCOL' and layer.source_group == '') or smooth_bump_ch:
        return

    layer_tree = get_tree(layer)

    if layer.type != 'VCOL':
        source_group = layer_tree.nodes.get(layer.source_group)
        source_ref = source_group.node_tree.nodes.get(layer.source)
        mapping_ref = source_group.node_tree.nodes.get(layer.mapping)

        # Create new source
        source = new_node(layer_tree, layer, 'source', source_ref.bl_idname)
        copy_node_props(source_ref, source)

        mapping = new_node(layer_tree, layer, 'mapping', 'ShaderNodeMapping')
        if mapping_ref: copy_node_props(mapping_ref, mapping)

        # Bring back layer modifier to original tree
        if layer.type == 'IMAGE':
            for mod in layer.modifiers:
                Modifier.add_modifier_nodes(mod, layer_tree, source_group.node_tree)
        else:
            move_mod_group(layer, source_group.node_tree, layer_tree)

        # Remove previous source
        remove_node(layer_tree, layer, 'source_group')
        remove_node(layer_tree, layer, 'source_n')
        remove_node(layer_tree, layer, 'source_s')
        remove_node(layer_tree, layer, 'source_e')
        remove_node(layer_tree, layer, 'source_w')

    remove_node(layer_tree, layer, 'uv_neighbor')

    if rearrange:
        # Reconnect outside nodes
        reconnect_layer_nodes(layer)

        # Rearrange nodes
        rearrange_layer_nodes(layer)

def set_mask_uv_neighbor(tree, layer, mask, mask_idx=-1):

    yp = layer.id_data.yp

    # Check if smooth bump channel is available
    smooth_bump_ch = get_smooth_bump_channel(layer)

    # Get channel that write height
    write_height_ch = get_write_height_normal_channel(layer)

    # Get mask index
    if mask_idx == -1:
        match = re.match(r'yp\.layers\[(\d+)\]\.masks\[(\d+)\]', mask.path_from_id())
        mask_idx = int(match.group(2))

    # Get chain
    chain = get_bump_chain(layer)

    if smooth_bump_ch and smooth_bump_ch.enable and (write_height_ch or mask_idx < chain):

        if mask.type == 'VCOL': 
            lib_name = lib.NEIGHBOR_FAKE
        else: lib_name = lib.get_neighbor_uv_tree_name(mask.texcoord_type, entity=mask)

        uv_neighbor, dirty = replace_new_node(tree, mask, 'uv_neighbor', 
                'ShaderNodeGroup', 'Spread Alpha Hack', lib_name, return_status=True, hard_replace=True)

        set_uv_neighbor_resolution(mask, uv_neighbor)

        return dirty

    return False

def enable_mask_source_tree(layer, mask, reconnect = False):

    # Check if source tree is already available
    if mask.type != 'VCOL' and mask.group_node != '': return

    layer_tree = get_tree(layer)

    # Create uv neighbor
    set_mask_uv_neighbor(layer_tree, layer, mask)

    #return

    if mask.type != 'VCOL':
        # Get current source for reference
        source_ref = layer_tree.nodes.get(mask.source)
        mapping_ref = layer_tree.nodes.get(mask.mapping)

        # Create mask tree
        mask_tree = bpy.data.node_groups.new(MASKGROUP_PREFIX + mask.name, 'ShaderNodeTree')

        # Create input and outputs
        mask_tree.inputs.new('NodeSocketVector', 'Vector')
        #mask_tree.outputs.new('NodeSocketColor', 'Color')
        mask_tree.outputs.new('NodeSocketFloat', 'Value')

        create_essential_nodes(mask_tree)

        # Copy nodes from reference
        #source = new_node(mask_tree, mask, 'source', source_ref.bl_idname)
        source = new_node(mask_tree, mask, 'source', 'ShaderNodeTexImage')
        copy_node_props(source_ref, source)
        #source.image = source_ref.image

        mapping = new_node(mask_tree, mask, 'mapping', 'ShaderNodeMapping')
        if mapping_ref: copy_node_props(mapping_ref, mapping)

        # Create source node group
        group_node = new_node(layer_tree, mask, 'group_node', 'ShaderNodeGroup', 'source_group')
        source_n = new_node(layer_tree, mask, 'source_n', 'ShaderNodeGroup', 'source_n')
        source_s = new_node(layer_tree, mask, 'source_s', 'ShaderNodeGroup', 'source_s')
        source_e = new_node(layer_tree, mask, 'source_e', 'ShaderNodeGroup', 'source_e')
        source_w = new_node(layer_tree, mask, 'source_w', 'ShaderNodeGroup', 'source_w')

        group_node.node_tree = mask_tree
        source_n.node_tree = mask_tree
        source_s.node_tree = mask_tree
        source_e.node_tree = mask_tree
        source_w.node_tree = mask_tree

        for mod in mask.modifiers:
            MaskModifier.add_modifier_nodes(mod, mask_tree, layer_tree)

        # Remove previous nodes
        layer_tree.nodes.remove(source_ref)
        if mapping_ref: layer_tree.nodes.remove(mapping_ref)

    if reconnect:
        # Reconnect outside nodes
        reconnect_layer_nodes(layer)

        # Rearrange nodes
        rearrange_layer_nodes(layer)

def disable_mask_source_tree(layer, mask, reconnect=False):

    # Check if source tree is already gone
    if mask.type != 'VCOL' and mask.group_node == '': return

    layer_tree = get_tree(layer)

    if mask.type != 'VCOL':

        mask_tree = get_mask_tree(mask)

        source_ref = mask_tree.nodes.get(mask.source)
        mapping_ref = mask_tree.nodes.get(mask.mapping)
        group_node = layer_tree.nodes.get(mask.group_node)

        # Create new nodes
        source = new_node(layer_tree, mask, 'source', source_ref.bl_idname)
        copy_node_props(source_ref, source)

        mapping = new_node(layer_tree, mask, 'mapping', 'ShaderNodeMapping')
        if mapping_ref: copy_node_props(mapping_ref, mapping)

        for mod in mask.modifiers:
            MaskModifier.add_modifier_nodes(mod, layer_tree, mask_tree)

        # Remove previous source
        remove_node(layer_tree, mask, 'group_node')
        remove_node(layer_tree, mask, 'source_n')
        remove_node(layer_tree, mask, 'source_s')
        remove_node(layer_tree, mask, 'source_e')
        remove_node(layer_tree, mask, 'source_w')
        remove_node(layer_tree, mask, 'tangent')
        remove_node(layer_tree, mask, 'bitangent')
        remove_node(layer_tree, mask, 'tangent_flip')
        remove_node(layer_tree, mask, 'bitangent_flip')

    remove_node(layer_tree, mask, 'uv_neighbor')

    if reconnect:
        # Reconnect outside nodes
        reconnect_layer_nodes(layer)

        # Rearrange nodes
        rearrange_layer_nodes(layer)

def check_create_height_pack(layer, tree, height_root_ch, height_ch):
    
    # Standard height pack unpack
    if height_root_ch.enable_smooth_bump:

        height_pack_ons = check_new_node(tree, height_ch, 'height_pack_ons', 
                'ShaderNodeCombineXYZ', 'Pack Height ONS')
        height_unpack_ons = check_new_node(tree, height_ch, 'height_unpack_ons', 
                'ShaderNodeSeparateXYZ', 'Unpack Height ONS')

        height_pack_ew = check_new_node(tree, height_ch, 'height_pack_ew', 
                'ShaderNodeCombineXYZ', 'Pack Height EW')
        height_unpack_ew = check_new_node(tree, height_ch, 'height_unpack_ew', 
                'ShaderNodeSeparateXYZ', 'Unpack Height EW')

    else:
        remove_node(tree, height_ch, 'height_pack_ons')
        remove_node(tree, height_ch, 'height_unpack_ons')
        remove_node(tree, height_ch, 'height_pack_ew')
        remove_node(tree, height_ch, 'height_unpack_ew')

    # Height pack unpack inside group
    if height_root_ch.enable_smooth_bump and layer.parent_idx != -1:

        height_alpha_pack_ons = check_new_node(tree, height_ch, 'height_alpha_pack_ons', 
                'ShaderNodeCombineXYZ', 'Pack Height ONS Alpha')
        height_alpha_unpack_ons = check_new_node(tree, height_ch, 'height_alpha_unpack_ons', 
                'ShaderNodeSeparateXYZ', 'Unpack Height ONS Alpha')
        height_alpha_pack_ew = check_new_node(tree, height_ch, 'height_alpha_pack_ew', 
                'ShaderNodeCombineXYZ', 'Pack Height EW Alpha')
        height_alpha_unpack_ew = check_new_node(tree, height_ch, 'height_alpha_unpack_ew', 
                'ShaderNodeSeparateXYZ', 'Unpack Height EW Alpha')

    else:
        remove_node(tree, height_ch, 'height_alpha_pack_ons')
        remove_node(tree, height_ch, 'height_alpha_unpack_ons')
        remove_node(tree, height_ch, 'height_alpha_pack_ew')
        remove_node(tree, height_ch, 'height_alpha_unpack_ew')

    if height_root_ch.enable_smooth_bump and layer.type == 'GROUP':

        height_group_unpack_ons = check_new_node(tree, height_ch, 'height_group_unpack_ons', 
                'ShaderNodeSeparateXYZ', 'Unpack Height Group ONS')
        height_group_unpack_ew = check_new_node(tree, height_ch, 'height_group_unpack_ew', 
                'ShaderNodeSeparateXYZ', 'Unpack Height Group EW')
        height_alpha_group_unpack_ons = check_new_node(tree, height_ch, 'height_alpha_group_unpack_ons', 
                'ShaderNodeSeparateXYZ', 'Unpack Height Alpha Group ONS')
        height_alpha_group_unpack_ew = check_new_node(tree, height_ch, 'height_alpha_group_unpack_ew', 
                'ShaderNodeSeparateXYZ', 'Unpack Height Alpha Group EW')
    else:
        remove_node(tree, height_ch, 'height_group_unpack_ons')
        remove_node(tree, height_ch, 'height_group_unpack_ew')
        remove_node(tree, height_ch, 'height_alpha_group_unpack_ons')
        remove_node(tree, height_ch, 'height_alpha_group_unpack_ew')

def check_create_spread_alpha(layer, tree, root_ch, ch):

    skip = False
    #if layer.type in {'BACKGROUND', 'GROUP'}: #or is_valid_to_remove_bump_nodes(layer, ch):
    if layer.type != 'IMAGE':
        skip = True

    if not skip and ch.normal_map_type != 'NORMAL_MAP': # and ch.enable_transition_bump:
        spread_alpha = replace_new_node(tree, ch, 'spread_alpha', 
                'ShaderNodeGroup', 'Spread Alpha Hack', lib.SPREAD_ALPHA)
    else:
        remove_node(tree, ch, 'spread_alpha')

    if not skip and root_ch.enable_smooth_bump and ch.normal_map_type != 'NORMAL_MAP': # and ch.enable_transition_bump:
        for d in neighbor_directions:
            bb = replace_new_node(tree, ch, 'spread_alpha_' + d, 
                    'ShaderNodeGroup', 'Spread Alpha ' + d, lib.SPREAD_ALPHA) 
    else:
        for d in neighbor_directions:
            remove_node(tree, ch, 'spread_alpha_' + d)

    #remove_node(tree, ch, 'bump_base')
    #for d in neighbor_directions:
    #    remove_node(tree, ch, 'bump_base_' + d)

def check_mask_mix_nodes(layer, tree=None, specific_mask=None, specific_ch=None):

    yp = layer.id_data.yp
    if not tree: tree = get_tree(layer)

    trans_bump = get_transition_bump_channel(layer)
    trans_bump_flip = trans_bump.transition_bump_flip if trans_bump else False

    chain = get_bump_chain(layer)

    for i, mask in enumerate(layer.masks):
        if specific_mask and mask != specific_mask: continue

        for j, c in enumerate(mask.channels):

            ch = layer.channels[j]
            root_ch = yp.channels[j]

            if specific_ch and ch != specific_ch: continue

            #if yp.disable_quick_toggle and not ch.enable:
            if not ch.enable or not layer.enable_masks or not mask.enable or not c.enable:
                remove_node(tree, c, 'mix')
                remove_node(tree, c, 'mix_n')
                if root_ch.type == 'NORMAL':
                    remove_node(tree, c, 'mix_s')
                    remove_node(tree, c, 'mix_e')
                    remove_node(tree, c, 'mix_w')
                    remove_node(tree, c, 'mix_pure')
                    remove_node(tree, c, 'mix_remains')
                    remove_node(tree, c, 'mix_normal')
                continue

            #if root_ch.type == 'NORMAL' and not trans_bump:
            #    chain = min(ch.transition_bump_chain, len(layer.masks))
            #elif trans_bump:
            #    chain = min(trans_bump.transition_bump_chain, len(layer.masks))
            #else: chain = -1

            mix = tree.nodes.get(c.mix)
            if not mix:
                mix = new_node(tree, c, 'mix', 'ShaderNodeMixRGB', 'Mask Blend')
                mix.blend_type = mask.blend_type
                mix.inputs[0].default_value = mask.intensity_value

            if root_ch.type == 'NORMAL':

                if i >= chain and trans_bump and ch == trans_bump:
                    mix_pure = tree.nodes.get(c.mix_pure)
                    if not mix_pure:
                        mix_pure = new_node(tree, c, 'mix_pure', 'ShaderNodeMixRGB', 'Mask Blend Pure')
                        mix_pure.blend_type = mask.blend_type
                        mix_pure.inputs[0].default_value = mask.intensity_value

                else:
                    remove_node(tree, c, 'mix_pure')

                if i >= chain and (
                    #(trans_bump and ch == trans_bump and ch.transition_bump_crease and not ch.write_height) or
                    (trans_bump and ch == trans_bump and ch.transition_bump_crease) or
                    (not trans_bump)
                    ):
                    mix_remains = tree.nodes.get(c.mix_remains)
                    if not mix_remains:
                        mix_remains = new_node(tree, c, 'mix_remains', 'ShaderNodeMixRGB', 'Mask Blend Remaining')
                        mix_remains.blend_type = mask.blend_type
                        mix_remains.inputs[0].default_value = mask.intensity_value
                else:
                    remove_node(tree, c, 'mix_remains')

                if (
                    #(not trans_bump and ch.normal_map_type in {'FINE_BUMP_MAP'}) or
                    #(trans_bump == ch and ch.transition_bump_type in {'FINE_BUMP_MAP', 'CURVED_BUMP_MAP'}) 
                    #ch.normal_map_type == 'FINE_BUMP_MAP' and
                    root_ch.enable_smooth_bump and
                    (ch.write_height or (not ch.write_height and i < chain))
                    #) and i < chain):
                    ):

                    for d in neighbor_directions:
                        mix = tree.nodes.get(getattr(c, 'mix_' + d))

                        if not mix:
                            mix = new_node(tree, c, 'mix_' + d, 'ShaderNodeMixRGB', 'Mask Blend ' + d)
                            mix.blend_type = mask.blend_type
                            mix.inputs[0].default_value = mask.intensity_value

                else:
                    for d in neighbor_directions:
                        remove_node(tree, c, 'mix_' + d)

                if layer.type == 'GROUP':
                    mix_normal = tree.nodes.get(c.mix_normal)
                    if not mix_normal:
                        mix_normal = new_node(tree, c, 'mix_normal', 'ShaderNodeMixRGB', 'Mask Normal')
                        mix_normal.blend_type = mask.blend_type
                        mix_normal.inputs[0].default_value = mask.intensity_value
                else:
                    remove_node(tree, c, 'mix_normal')

            else: 
                if (trans_bump and i >= chain and (
                    (trans_bump_flip and ch.enable_transition_ramp) or 
                    #(not trans_bump_flip and ch.enable_transition_ramp and ch.transition_ramp_intensity_unlink) or
                    (not trans_bump_flip and ch.enable_transition_ao)
                    )):
                    mix_n = tree.nodes.get(c.mix_n)

                    if not mix_n:
                        mix_n = new_node(tree, c, 'mix_n', 'ShaderNodeMixRGB', 'Mask Blend n')
                        mix_n.blend_type = mask.blend_type
                        mix_n.inputs[0].default_value = mask.intensity_value
                else:
                    remove_node(tree, c, 'mix_n')

def check_mask_source_tree(layer, specific_mask=None): #, ch=None):

    yp = layer.id_data.yp

    smooth_bump_ch = get_smooth_bump_channel(layer)
    write_height_ch = get_write_height_normal_channel(layer)
    chain = get_bump_chain(layer)

    for i, mask in enumerate(layer.masks):
        if specific_mask and specific_mask != mask: continue

        if smooth_bump_ch and smooth_bump_ch.enable and (write_height_ch or i < chain):
            enable_mask_source_tree(layer, mask)
        else: disable_mask_source_tree(layer, mask)

def remove_tangent_sign_vcol(obj, uv_name):
    vcol = obj.data.vertex_colors.get('__tsign_' + uv_name)
    if vcol: vcol = obj.data.vertex_colors.remove(vcol)

def refresh_tangent_sign_vcol(obj, uv_name):

    # Set vertex color of bitangent sign
    if hasattr(obj.data, 'uv_textures'):
        uv_layers = obj.data.uv_textures
    else: uv_layers = obj.data.uv_layers

    uv_layer = uv_layers.get(uv_name)
    if uv_layer:

        # Set uv as active
        ori_layer = uv_layers.active
        uv_layers.active = uv_layer

        # Cannot do this on edit mode
        ori_mode = obj.mode
        if ori_mode == 'EDIT':
            bpy.ops.object.mode_set(mode='OBJECT')

        obj.data.calc_tangents()

        vcol = obj.data.vertex_colors.get('__tsign_' + uv_name)
        if not vcol:
            try: vcol = obj.data.vertex_colors.new(name='__tsign_' + uv_name)
            except: return None

        i = 0
        for poly in obj.data.polygons:
            for idx in poly.loop_indices:
                vert = obj.data.loops[idx]
                bs = max(vert.bitangent_sign, 0.0)
                if bpy.app.version_string.startswith('2.8'):
                    vcol.data[i].color = (bs, bs, bs, 1.0)
                else: vcol.data[i].color = (bs, bs, bs)
                i += 1

        # Recover active uv
        uv_layers.active = ori_layer

        # Back to edit mode if originally from there
        if ori_mode == 'EDIT':
            bpy.ops.object.mode_set(mode='EDIT')

        return vcol

    return None

def update_enable_tangent_sign_hacks(self, context):
    node = get_active_ypaint_node()
    tree = node.node_tree
    yp = tree.yp
    #ypui = context.window_manager.ypui
    ypui = self
    obj = context.object

    for uv in yp.uvs:
        tangent_process = tree.nodes.get(uv.tangent_process)
        if tangent_process:
            if yp.enable_tangent_sign_hacks:
                tangent_process.inputs['Blender 2.8 Cycles Hack'].default_value = 1.0
                tsign = tangent_process.node_tree.nodes.get('_tangent_sign')
                vcol = refresh_tangent_sign_vcol(obj, uv.name)
                if vcol: tsign.attribute_name = vcol.name
            else:
                tangent_process.inputs['Blender 2.8 Cycles Hack'].default_value = 0.0
                remove_tangent_sign_vcol(obj, uv.name)

def create_uv_nodes(yp, uv_name, obj):

    tree = yp.id_data
    ypui = bpy.context.window_manager.ypui

    uv = yp.uvs.add()
    uv.name = uv_name

    uv_map = new_node(tree, uv, 'uv_map', 'ShaderNodeUVMap', uv_name)
    uv_map.uv_map = uv_name

    # Create tangent process which output both tangent and bitangent
    tangent_process = new_node(tree, uv, 'tangent_process', 'ShaderNodeGroup', uv_name + ' Tangent Process')
    tangent_process.node_tree = get_node_tree_lib(lib.TANGENT_PROCESS)
    duplicate_lib_node_tree(tangent_process)

    tangent_process.inputs['Backface Always Up'].default_value = 1.0 if yp.enable_backface_always_up else 0.0

    # Set values inside tangent process
    tp_nodes = tangent_process.node_tree.nodes
    node = tp_nodes.get('_tangent')
    node.uv_map = uv_name
    node = tp_nodes.get('_tangent_from_norm')
    node.uv_map = uv_name
    node = tp_nodes.get('_bitangent_from_norm')
    node.uv_map = uv_name

    if yp.enable_tangent_sign_hacks:
        tangent_process.inputs['Blender 2.8 Cycles Hack'].default_value = 1.0
        node = tp_nodes.get('_tangent_sign')

        vcol = refresh_tangent_sign_vcol(obj, uv_name)
        if vcol: node.attribute_name = vcol.name
    else:
        tangent_process.inputs['Blender 2.8 Cycles Hack'].default_value = 0.0

def check_parallax_process_outputs(parallax, uv_name, remove=False):

    outp = parallax.node_tree.outputs.get(uv_name)
    if remove and outp:
        parallax.node_tree.outputs.remove(outp)
    elif not remove and not outp:
        outp = parallax.node_tree.outputs.new('NodeSocketVector', uv_name)

def check_parallax_mix(tree, uv, baked=False, remove=False):

    if baked: parallax_mix = tree.nodes.get(uv.baked_parallax_mix)
    else: parallax_mix = tree.nodes.get(uv.parallax_mix)

    if remove and parallax_mix:
        if baked: remove_node(tree, uv, 'baked_parallax_mix')
        else: remove_node(tree, uv, 'parallax_mix')
        #tree.nodes.remove(parallax_mix)
    elif not remove and not parallax_mix:
        if baked: parallax_mix = new_node(tree, uv, 'baked_parallax_mix', 'ShaderNodeMixRGB', uv.name + ' Final Mix')
        else: parallax_mix = new_node(tree, uv, 'parallax_mix', 'ShaderNodeMixRGB', uv.name + ' Final Mix')

def check_non_uv_parallax_mix(tree, texcoord_name, remove=False):

    parallax_mix = tree.nodes.get(PARALLAX_MIX_PREFIX + TEXCOORD_IO_PREFIX + texcoord_name)

    if remove and parallax_mix:
        tree.nodes.remove(parallax_mix)
    elif not remove and not parallax_mix:
        parallax_mix = tree.nodes.new('ShaderNodeMixRGB')
        parallax_mix.name = PARALLAX_MIX_PREFIX + TEXCOORD_IO_PREFIX + texcoord_name
        parallax_mix.label = texcoord_name + ' Final Mix'

def check_start_delta_uv_inputs(tree, uv_name, remove=False):

    start_uv_name = uv_name + START_UV
    delta_uv_name = uv_name + DELTA_UV

    start = tree.inputs.get(start_uv_name)
    if remove and start:
        tree.inputs.remove(start)
    elif not remove and not start:
        tree.inputs.new('NodeSocketVector', start_uv_name)

    delta = tree.inputs.get(delta_uv_name)
    if remove and delta:
        tree.inputs.remove(delta)
    elif not remove and not delta:
        tree.inputs.new('NodeSocketVector', delta_uv_name)

def check_current_uv_outputs(tree, uv_name, remove=False):
    current_uv_name = uv_name + CURRENT_UV

    current = tree.outputs.get(current_uv_name)
    if remove and current:
        tree.outputs.remove(current)
    elif not remove and not current:
        tree.outputs.new('NodeSocketVector', current_uv_name)

def check_current_uv_inputs(tree, uv_name, remove=False):
    current_uv_name = uv_name + CURRENT_UV

    current = tree.inputs.get(current_uv_name)
    if remove and current:
        tree.inputs.remove(current)
    elif not remove and not current:
        tree.inputs.new('NodeSocketVector', current_uv_name)

def check_iterate_current_uv_mix(tree, uv, baked=False, remove=False):

    if baked: current_uv_mix = tree.nodes.get(uv.baked_parallax_current_uv_mix)
    else: current_uv_mix = tree.nodes.get(uv.parallax_current_uv_mix)

    if remove and current_uv_mix:
        if baked: remove_node(tree, uv, 'baked_parallax_current_uv_mix')
        else: remove_node(tree, uv, 'parallax_current_uv_mix')
    elif not remove and not current_uv_mix:
        if baked: current_uv_mix = new_node(tree, uv, 'baked_parallax_current_uv_mix', 
                'ShaderNodeMixRGB', uv.name + CURRENT_UV)
        else: current_uv_mix = new_node(tree, uv, 'parallax_current_uv_mix', 
                'ShaderNodeMixRGB', uv.name + CURRENT_UV)

def check_non_uv_iterate_current_mix(tree, texcoord_name, remove=False):

    current_mix = tree.nodes.get(PARALLAX_CURRENT_MIX_PREFIX + TEXCOORD_IO_PREFIX + texcoord_name)

    if remove and current_mix:
        tree.nodes.remove(current_mix)
    elif not remove and not current_mix:
        current_mix = tree.nodes.new('ShaderNodeMixRGB')
        current_mix.name = PARALLAX_CURRENT_MIX_PREFIX + TEXCOORD_IO_PREFIX + texcoord_name
        current_mix.label = texcoord_name + ' Current Mix'

def check_depth_source_calculation(tree, uv, baked=False, remove=False):

    if baked: delta_uv = tree.nodes.get(uv.baked_parallax_delta_uv)
    else: delta_uv = tree.nodes.get(uv.parallax_delta_uv)

    if remove and delta_uv:
        if baked: remove_node(tree, uv, 'baked_parallax_delta_uv')
        else: remove_node(tree, uv, 'parallax_delta_uv')
        #tree.nodes.remove(delta_uv)
    elif not remove and not delta_uv:
        if baked: delta_uv = new_node(tree, uv, 'baked_parallax_delta_uv', 'ShaderNodeMixRGB', uv.name + DELTA_UV)
        else: delta_uv = new_node(tree, uv, 'parallax_delta_uv', 'ShaderNodeMixRGB', uv.name + DELTA_UV)
        delta_uv.inputs[0].default_value = 1.0
        delta_uv.blend_type = 'MULTIPLY'

    if baked: current_uv = tree.nodes.get(uv.baked_parallax_current_uv)
    else: current_uv = tree.nodes.get(uv.parallax_current_uv)

    if remove and current_uv:
        if baked: remove_node(tree, uv, 'baked_parallax_current_uv')
        else: remove_node(tree, uv, 'parallax_current_uv')
        #tree.nodes.remove(current_uv)
    elif not remove and not current_uv:
        if baked: current_uv = new_node(tree, uv, 'baked_parallax_current_uv', 'ShaderNodeVectorMath', uv.name + CURRENT_UV)
        else: current_uv = new_node(tree, uv, 'parallax_current_uv', 'ShaderNodeVectorMath', uv.name + CURRENT_UV)
        current_uv.operation = 'SUBTRACT'

def check_non_uv_depth_source_calculation(tree, texcoord_name, remove=False):

    delta = tree.nodes.get(PARALLAX_DELTA_PREFIX + TEXCOORD_IO_PREFIX + texcoord_name)

    if remove and delta:
        tree.nodes.remove(delta)
    elif not remove and not delta:
        delta = tree.nodes.new('ShaderNodeMixRGB')
        delta.name = PARALLAX_DELTA_PREFIX + TEXCOORD_IO_PREFIX + texcoord_name
        delta.label = texcoord_name + ' Delta'
        delta.inputs[0].default_value = 1.0
        delta.blend_type = 'MULTIPLY'

    current = tree.nodes.get(PARALLAX_CURRENT_PREFIX + TEXCOORD_IO_PREFIX + texcoord_name)

    if remove and current:
        tree.nodes.remove(current)
    elif not remove and not current:
        current = tree.nodes.new('ShaderNodeVectorMath')
        current.name = PARALLAX_CURRENT_PREFIX + TEXCOORD_IO_PREFIX + texcoord_name
        current.label = texcoord_name + ' Current'
        current.operation = 'SUBTRACT'

def refresh_parallax_depth_source_layers(yp, parallax): #, disp_ch):

    depth_source_0 = parallax.node_tree.nodes.get('_depth_source_0')
    tree = depth_source_0.node_tree

    for layer in yp.layers:
        node = tree.nodes.get(layer.depth_group_node)
        if not node:
            n = yp.id_data.nodes.get(layer.group_node)
            node = new_node(tree, layer, 'depth_group_node', 'ShaderNodeGroup', layer.name)
            node.node_tree = n.node_tree

def refresh_parallax_depth_img(yp, parallax, disp_img): #, disp_ch):

    depth_source_0 = parallax.node_tree.nodes.get('_depth_source_0')
    tree = depth_source_0.node_tree

    height_map = tree.nodes.get(HEIGHT_MAP)
    if not height_map:
        height_map = tree.nodes.new('ShaderNodeTexImage')
        height_map.name = HEIGHT_MAP
        if hasattr(height_map, 'color_space'):
            height_map.color_space = 'NONE'

    height_map.image = disp_img

def check_parallax_prep_nodes(yp, unused_uvs=[], unused_texcoords=[], baked=False):

    tree = yp.id_data

    # Standard height channel is same as parallax channel (for now?)
    height_ch = get_root_height_channel(yp)
    if not height_ch: return

    if baked: num_of_layers = int(height_ch.baked_parallax_num_of_layers)
    else: num_of_layers = int(height_ch.parallax_num_of_layers)

    max_height = get_displacement_max_height(height_ch)

    # Create parallax preparations for uvs
    for uv in yp.uvs:
        if uv in unused_uvs: continue
        if not height_ch.enable_parallax:
            remove_node(tree, uv, 'parallax_prep')
        else:
            parallax_prep = tree.nodes.get(uv.parallax_prep)
            if not parallax_prep:
                parallax_prep = new_node(tree, uv, 'parallax_prep', 'ShaderNodeGroup', 
                        uv.name + ' Parallax Preparation')
                parallax_prep.node_tree = get_node_tree_lib(lib.PARALLAX_OCCLUSION_PREP)

            #parallax_prep.inputs['depth_scale'].default_value = height_ch.displacement_height_ratio
            parallax_prep.inputs['depth_scale'].default_value = max_height
            parallax_prep.inputs['ref_plane'].default_value = height_ch.parallax_ref_plane
            parallax_prep.inputs['Rim Hack'].default_value = 1.0 if height_ch.parallax_rim_hack else 0.0
            parallax_prep.inputs['Rim Hack Hardness'].default_value = height_ch.parallax_rim_hack_hardness
            parallax_prep.inputs['layer_depth'].default_value = 1.0 / num_of_layers

    # Create parallax preparations for texcoords other than UV
    for tc in texcoord_lists:

        parallax_prep = tree.nodes.get(tc + PARALLAX_PREP_SUFFIX)

        if tc not in unused_texcoords and height_ch.enable_parallax:

            if not parallax_prep:
                parallax_prep = tree.nodes.new('ShaderNodeGroup')
                if tc in {'Generated', 'Normal', 'Object'}:
                    parallax_prep.node_tree = lib.get_node_tree_lib(lib.PARALLAX_OCCLUSION_PREP_OBJECT)
                elif tc in {'Camera', 'Window', 'Reflection'}: 
                    parallax_prep.node_tree = lib.get_node_tree_lib(lib.PARALLAX_OCCLUSION_PREP_CAMERA)
                else:
                    parallax_prep.node_tree = lib.get_node_tree_lib(lib.PARALLAX_OCCLUSION_PREP)
                parallax_prep.name = parallax_prep.label = tc + PARALLAX_PREP_SUFFIX

            parallax_prep.inputs['depth_scale'].default_value = max_height
            parallax_prep.inputs['ref_plane'].default_value = height_ch.parallax_ref_plane
            parallax_prep.inputs['Rim Hack'].default_value = 1.0 if height_ch.parallax_rim_hack else 0.0
            parallax_prep.inputs['Rim Hack Hardness'].default_value = height_ch.parallax_rim_hack_hardness
            parallax_prep.inputs['layer_depth'].default_value = 1.0 / num_of_layers

        elif parallax_prep:
            tree.nodes.remove(parallax_prep)

def clear_parallax_node_data(yp, parallax, baked=False):

    depth_source_0 = parallax.node_tree.nodes.get('_depth_source_0')
    parallax_loop = parallax.node_tree.nodes.get('_parallax_loop')
    iterate = parallax_loop.node_tree.nodes.get('_iterate')

    # Remove iterate depth
    counter = 0
    while True:
        it = parallax_loop.node_tree.nodes.get('_iterate_depth_' + str(counter))

        if it and it.node_tree:
            bpy.data.node_groups.remove(it.node_tree)
        else: break

        counter += 1

    # Remove node trees
    bpy.data.node_groups.remove(iterate.node_tree)
    bpy.data.node_groups.remove(parallax_loop.node_tree)
    bpy.data.node_groups.remove(depth_source_0.node_tree)

    # Clear parallax uv node names
    for uv in yp.uvs:
        if not baked:
            uv.parallax_current_uv_mix = ''
            uv.parallax_current_uv = ''
            uv.parallax_delta_uv = ''
            uv.parallax_mix = ''
        else:
            uv.baked_parallax_current_uv_mix = ''
            uv.baked_parallax_current_uv = ''
            uv.baked_parallax_delta_uv = ''
            uv.baked_parallax_mix = ''

    # Clear parallax layer node names
    if not baked:
        for layer in yp.layers:
            layer.depth_group_node = ''

def check_adaptive_subdiv_nodes(yp, height_ch, baked=False):

    if baked and height_ch.enable_subdiv_setup and height_ch.subdiv_adaptive:
        pass
    else:
        pass

def check_parallax_node(yp, height_ch, unused_uvs=[], unused_texcoords=[], baked=False):

    tree = yp.id_data

    # Standard height channel is same as parallax channel (for now?)
    #height_ch = get_root_height_channel(yp)
    #if not height_ch: return

    if baked: num_of_layers = int(height_ch.baked_parallax_num_of_layers)
    else: num_of_layers = int(height_ch.parallax_num_of_layers)

    # Get parallax node
    node_name = BAKED_PARALLAX if baked else PARALLAX
    parallax = tree.nodes.get(node_name)
    baked_parallax_filter = tree.nodes.get(BAKED_PARALLAX_FILTER)

    if (not height_ch.enable_parallax or 
            (baked and not yp.use_baked) or (not baked and yp.use_baked) or
            (yp.use_baked and height_ch.enable_subdiv_setup and not height_ch.subdiv_adaptive)
            ):
        if parallax:
            clear_parallax_node_data(yp, parallax, baked)
            simple_remove_node(tree, parallax, True)
            if baked_parallax_filter: simple_remove_node(tree, baked_parallax_filter, True)
        return

    # Displacement image needed for baked parallax
    disp_img = None
    if baked:
        baked_disp = tree.nodes.get(height_ch.baked_disp)
        if baked_disp:
            disp_img = baked_disp.image
        else:
            return

    # Create parallax node
    if not parallax:
        parallax = tree.nodes.new('ShaderNodeGroup')
        parallax.name = node_name

        parallax.label = 'Parallax Occlusion Mapping'
        if baked: parallax.label = 'Baked ' + parallax.label

        parallax.node_tree = get_node_tree_lib(lib.PARALLAX_OCCLUSION_PROC)
        duplicate_lib_node_tree(parallax)

        depth_source_0 = parallax.node_tree.nodes.get('_depth_source_0')
        depth_source_0.node_tree.name += '_Copy'
        
        parallax_loop = parallax.node_tree.nodes.get('_parallax_loop')
        duplicate_lib_node_tree(parallax_loop)

        #iterate = parallax_loop.node_tree.nodes.get('_iterate_0')
        iterate = parallax_loop.node_tree.nodes.get('_iterate')
        duplicate_lib_node_tree(iterate)

    # Check baked parallax filter
    if baked and height_ch.enable_subdiv_setup and height_ch.subdiv_adaptive:
        if not baked_parallax_filter:
            baked_parallax_filter = tree.nodes.new('ShaderNodeGroup')
            baked_parallax_filter.name = BAKED_PARALLAX_FILTER
            baked_parallax_filter.node_tree = get_node_tree_lib(lib.ENGINE_FILTER)
            baked_parallax_filter.label = 'Baked Parallax Filter'
    elif baked_parallax_filter:
        simple_remove_node(tree, baked_parallax_filter, True)

    parallax_loop = parallax.node_tree.nodes.get('_parallax_loop')

    parallax.inputs['layer_depth'].default_value = 1.0 / num_of_layers

    if baked:
        refresh_parallax_depth_img(yp, parallax, disp_img)
    else: refresh_parallax_depth_source_layers(yp, parallax)

    depth_source_0 = parallax.node_tree.nodes.get('_depth_source_0')
    parallax_loop = parallax.node_tree.nodes.get('_parallax_loop')
    #iterate = parallax_loop.node_tree.nodes.get('_iterate_0')
    iterate = parallax_loop.node_tree.nodes.get('_iterate')
    #iterate_group_0 = parallax_loop.node_tree.nodes.get('_iterate_group_0')

    # Create IO and nodes for UV
    for uv in yp.uvs:

        if (baked and yp.baked_uv_name != uv.name) or uv in unused_uvs:

            # Delete other uv io
            check_parallax_process_outputs(parallax, uv.name, remove=True)
            check_start_delta_uv_inputs(parallax.node_tree, uv.name, remove=True)
            check_parallax_mix(parallax.node_tree, uv, baked, remove=True)

            check_start_delta_uv_inputs(depth_source_0.node_tree, uv.name, remove=True)
            check_current_uv_outputs(depth_source_0.node_tree, uv.name, remove=True)
            check_depth_source_calculation(depth_source_0.node_tree, uv, baked, remove=True)

            check_start_delta_uv_inputs(parallax_loop.node_tree, uv.name, remove=True)
            check_current_uv_outputs(parallax_loop.node_tree, uv.name, remove=True)
            check_current_uv_inputs(parallax_loop.node_tree, uv.name, remove=True)

            check_start_delta_uv_inputs(iterate.node_tree, uv.name, remove=True)
            check_current_uv_outputs(iterate.node_tree, uv.name, remove=True)
            check_current_uv_inputs(iterate.node_tree, uv.name, remove=True)
            check_iterate_current_uv_mix(iterate.node_tree, uv, baked, remove=True)

            #check_start_delta_uv_inputs(iterate_group_0.node_tree, uv.name, remove=True)
            #check_current_uv_outputs(iterate_group_0.node_tree, uv.name, remove=True)
            #check_current_uv_inputs(iterate_group_0.node_tree, uv.name, remove=True)

            continue

        check_parallax_process_outputs(parallax, uv.name)
        check_start_delta_uv_inputs(parallax.node_tree, uv.name)
        check_parallax_mix(parallax.node_tree, uv, baked)

        check_start_delta_uv_inputs(depth_source_0.node_tree, uv.name)
        check_current_uv_outputs(depth_source_0.node_tree, uv.name)
        check_depth_source_calculation(depth_source_0.node_tree, uv, baked)

        check_start_delta_uv_inputs(parallax_loop.node_tree, uv.name)
        check_current_uv_outputs(parallax_loop.node_tree, uv.name)
        check_current_uv_inputs(parallax_loop.node_tree, uv.name)

        check_start_delta_uv_inputs(iterate.node_tree, uv.name)
        check_current_uv_outputs(iterate.node_tree, uv.name)
        check_current_uv_inputs(iterate.node_tree, uv.name)
        check_iterate_current_uv_mix(iterate.node_tree, uv, baked)

        #check_start_delta_uv_inputs(iterate_group_0.node_tree, uv.name)
        #check_current_uv_outputs(iterate_group_0.node_tree, uv.name)
        #check_current_uv_inputs(iterate_group_0.node_tree, uv.name)

    # Baked parallax occlusion doesn't have to deal with non uv texture coordinates
    if not baked:

        # Create IO and nodes for Non-UV Texture Coordinates
        for tc in texcoord_lists:

            # Delete unused non UV io and nodes
            if tc in unused_texcoords:
                check_parallax_process_outputs(parallax, TEXCOORD_IO_PREFIX + tc, remove=True)
                check_start_delta_uv_inputs(parallax.node_tree, TEXCOORD_IO_PREFIX + tc, remove=True)
                check_non_uv_parallax_mix(parallax.node_tree, tc, remove=True)

                check_start_delta_uv_inputs(depth_source_0.node_tree, TEXCOORD_IO_PREFIX + tc, remove=True)
                check_current_uv_outputs(depth_source_0.node_tree, TEXCOORD_IO_PREFIX + tc, remove=True)
                check_non_uv_depth_source_calculation(depth_source_0.node_tree, tc, remove=True)

                check_start_delta_uv_inputs(parallax_loop.node_tree, TEXCOORD_IO_PREFIX + tc, remove=True)
                check_current_uv_outputs(parallax_loop.node_tree, TEXCOORD_IO_PREFIX + tc, remove=True)
                check_current_uv_inputs(parallax_loop.node_tree, TEXCOORD_IO_PREFIX + tc, remove=True)

                check_start_delta_uv_inputs(iterate.node_tree, TEXCOORD_IO_PREFIX + tc, remove=True)
                check_current_uv_outputs(iterate.node_tree, TEXCOORD_IO_PREFIX + tc, remove=True)
                check_current_uv_inputs(iterate.node_tree, TEXCOORD_IO_PREFIX + tc, remove=True)
                check_non_uv_iterate_current_mix(iterate.node_tree, tc, remove=True)

                #check_start_delta_uv_inputs(iterate_group_0.node_tree, TEXCOORD_IO_PREFIX + tc, remove=True)
                #check_current_uv_outputs(iterate_group_0.node_tree, TEXCOORD_IO_PREFIX + tc, remove=True)
                #check_current_uv_inputs(iterate_group_0.node_tree, TEXCOORD_IO_PREFIX + tc, remove=True)

                continue

            check_parallax_process_outputs(parallax, TEXCOORD_IO_PREFIX + tc)
            check_start_delta_uv_inputs(parallax.node_tree, TEXCOORD_IO_PREFIX + tc)
            check_non_uv_parallax_mix(parallax.node_tree, tc)

            check_start_delta_uv_inputs(depth_source_0.node_tree, TEXCOORD_IO_PREFIX + tc)
            check_current_uv_outputs(depth_source_0.node_tree, TEXCOORD_IO_PREFIX + tc)
            check_non_uv_depth_source_calculation(depth_source_0.node_tree, tc)

            check_start_delta_uv_inputs(parallax_loop.node_tree, TEXCOORD_IO_PREFIX + tc)
            check_current_uv_outputs(parallax_loop.node_tree, TEXCOORD_IO_PREFIX + tc)
            check_current_uv_inputs(parallax_loop.node_tree, TEXCOORD_IO_PREFIX + tc)

            check_start_delta_uv_inputs(iterate.node_tree, TEXCOORD_IO_PREFIX + tc)
            check_current_uv_outputs(iterate.node_tree, TEXCOORD_IO_PREFIX + tc)
            check_current_uv_inputs(iterate.node_tree, TEXCOORD_IO_PREFIX + tc)
            check_non_uv_iterate_current_mix(iterate.node_tree, tc)

            #check_start_delta_uv_inputs(iterate_group_0.node_tree, TEXCOORD_IO_PREFIX + tc)
            #check_current_uv_outputs(iterate_group_0.node_tree, TEXCOORD_IO_PREFIX + tc)
            #check_current_uv_inputs(iterate_group_0.node_tree, TEXCOORD_IO_PREFIX + tc)

    #create_delete_iterate_nodes(parallax_loop.node_tree, num_of_layers)
    #create_delete_iterate_nodes_(parallax_loop.node_tree, num_of_layers)
    create_delete_iterate_nodes__(parallax_loop.node_tree, num_of_layers)
    #update_displacement_height_ratio(height_ch)

def remove_uv_nodes(uv, obj):
    tree = uv.id_data
    yp = tree.yp

    remove_node(tree, uv, 'uv_map')
    remove_node(tree, uv, 'tangent_process')
    remove_node(tree, uv, 'tangent')
    remove_node(tree, uv, 'tangent_flip')
    remove_node(tree, uv, 'bitangent')
    remove_node(tree, uv, 'bitangent_flip')
    remove_node(tree, uv, 'parallax_prep')

    remove_tangent_sign_vcol(obj, uv.name)

    #yp.uvs.remove(uv)

def check_uv_nodes(yp):

    # Check for UV needed
    uv_names = []

    # Get active object
    obj = bpy.context.object

    dirty = False

    if obj.type == 'MESH':

        # Check uv layers of mesh objects
        if hasattr(obj.data, 'uv_textures'):
            uv_layers = obj.data.uv_textures
        else: uv_layers = obj.data.uv_layers

        for uv_layer in uv_layers:
            if uv_layer.name == TEMP_UV: continue
            uv = yp.uvs.get(uv_layer.name)
            if not uv: 
                dirty = True
                create_uv_nodes(yp, uv_layer.name, obj)
            if uv_layer.name not in uv_names: uv_names.append(uv_layer.name)

    # Get unused uv objects
    unused_uvs = []
    unused_ids = []
    for i, uv in reversed(list(enumerate(yp.uvs))):
        if uv.name not in uv_names:
            unused_uvs.append(uv)
            unused_ids.append(i)

    # Check non uv texcoords
    used_texcoords = []
    for layer in yp.layers:
        if layer.texcoord_type != 'UV' and layer.texcoord_type not in used_texcoords:
            used_texcoords.append(layer.texcoord_type)

            for mask in layer.masks:
                if mask.texcoord_type != 'UV' and mask.texcoord_type not in used_texcoords:
                    used_texcoords.append(mask.texcoord_type)

    # Check for unused texcoords
    unused_texcoords = []
    for tc in texcoord_lists:
        if tc not in used_texcoords:
            unused_texcoords.append(tc)

    # Check parallax preparation nodes
    check_parallax_prep_nodes(yp, unused_uvs, unused_texcoords, baked=yp.use_baked)

    # Get height channel
    height_ch = get_root_height_channel(yp)
    if not height_ch: return

    # Check standard parallax
    check_parallax_node(yp, height_ch, unused_uvs, unused_texcoords)

    # Check baked parallax
    check_parallax_node(yp, height_ch, unused_uvs, baked=True)

    # Update max height to parallax nodes
    update_displacement_height_ratio(height_ch)

    # Remove unused uv objects
    for i in unused_ids:
        uv = yp.uvs[i]
        remove_uv_nodes(uv, obj)
        dirty = True
        yp.uvs.remove(i)

    return dirty

def remove_layer_normal_channel_nodes(root_ch, layer, ch, tree=None):

    if not tree: tree = get_tree(layer)

    # Remove neighbor related nodes
    if root_ch.enable_smooth_bump:
        disable_layer_source_tree(layer, False)
        Modifier.disable_modifiers_tree(ch, False)

    remove_node(tree, ch, 'spread_alpha')
    remove_node(tree, ch, 'spread_alpha_n')
    remove_node(tree, ch, 'spread_alpha_s')
    remove_node(tree, ch, 'spread_alpha_e')
    remove_node(tree, ch, 'spread_alpha_w')

    remove_node(tree, ch, 'height_proc')
    remove_node(tree, ch, 'height_blend')
    remove_node(tree, ch, 'height_blend_n')
    remove_node(tree, ch, 'height_blend_s')
    remove_node(tree, ch, 'height_blend_e')
    remove_node(tree, ch, 'height_blend_w')

    remove_node(tree, ch, 'normal_proc')
    remove_node(tree, ch, 'normal_flip')

def check_channel_normal_map_nodes(tree, layer, root_ch, ch, need_reconnect=False):

    #print("Checking channel normal map nodes. Layer: " + layer.name + ' Channel: ' + root_ch.name)

    yp = layer.id_data.yp

    if root_ch.type != 'NORMAL': return need_reconnect

    # Check mask source tree
    check_mask_source_tree(layer) #, ch)

    # Check mask mix nodes
    check_mask_mix_nodes(layer, tree)

    # Return if channel is disabled
    if not ch.enable:
        remove_layer_normal_channel_nodes(root_ch, layer, ch, tree)

        return need_reconnect

    # Check height pack/unpack
    check_create_height_pack(layer, tree, root_ch, ch)

    # Check spread alpha if its needed
    check_create_spread_alpha(layer, tree, root_ch, ch)

    # Remove neighbor related nodes
    if root_ch.enable_smooth_bump:
        enable_layer_source_tree(layer)
        Modifier.enable_modifiers_tree(ch)
    else:
        disable_layer_source_tree(layer, False)
        Modifier.disable_modifiers_tree(ch, False)

    #mute = not layer.enable or not ch.enable

    max_height = get_displacement_max_height(root_ch, layer)
    update_displacement_height_ratio(root_ch)

    # Height Process
    if ch.normal_map_type == 'NORMAL_MAP':
        if root_ch.enable_smooth_bump:
            if ch.enable_transition_bump:
                if ch.transition_bump_crease and not ch.transition_bump_flip:
                    lib_name = lib.HEIGHT_PROCESS_TRANSITION_SMOOTH_NORMAL_MAP_CREASE
                else: 
                    lib_name = lib.HEIGHT_PROCESS_TRANSITION_SMOOTH_NORMAL_MAP
            else: 
                lib_name = lib.HEIGHT_PROCESS_SMOOTH_NORMAL_MAP

        else: 
            if ch.enable_transition_bump:
                if ch.transition_bump_crease and not ch.transition_bump_flip:
                    lib_name = lib.HEIGHT_PROCESS_TRANSITION_NORMAL_MAP_CREASE
                else: 
                    lib_name = lib.HEIGHT_PROCESS_TRANSITION_NORMAL_MAP
            else: 
                lib_name = lib.HEIGHT_PROCESS_NORMAL_MAP
    else:
        if root_ch.enable_smooth_bump:
            if ch.enable_transition_bump:
                if ch.transition_bump_crease and not ch.transition_bump_flip:
                    lib_name = lib.HEIGHT_PROCESS_TRANSITION_SMOOTH_CREASE
                elif ch.transition_bump_chain == 0:
                    lib_name = lib.HEIGHT_PROCESS_TRANSITION_SMOOTH_ZERO_CHAIN
                else:
                    lib_name = lib.HEIGHT_PROCESS_TRANSITION_SMOOTH
            else:
                lib_name = lib.HEIGHT_PROCESS_SMOOTH
        else: 
            if ch.enable_transition_bump:
                if ch.transition_bump_crease and not ch.transition_bump_flip:
                    lib_name = lib.HEIGHT_PROCESS_TRANSITION_CREASE
                else:
                    lib_name = lib.HEIGHT_PROCESS_TRANSITION
            else:
                lib_name = lib.HEIGHT_PROCESS

        # Group lib
        if layer.type == 'GROUP':
            lib_name += ' Group'

    height_proc, need_reconnect = replace_new_node(
            tree, ch, 'height_proc', 'ShaderNodeGroup', 'Height Process', 
            lib_name, return_status = True, hard_replace=True, dirty=need_reconnect)

    if ch.normal_map_type == 'NORMAL_MAP':
        if ch.enable_transition_bump:
            height_proc.inputs['Bump Height'].default_value = get_transition_bump_max_distance(ch)
        else: height_proc.inputs['Bump Height'].default_value = ch.bump_distance
    else:
        if layer.type != 'GROUP':
            height_proc.inputs['Value Max Height'].default_value = ch.bump_distance
        if ch.enable_transition_bump:
            height_proc.inputs['Delta'].default_value = get_transition_disp_delta(layer, ch)
            height_proc.inputs['Transition Max Height'].default_value = get_transition_bump_max_distance(ch)

    #height_proc.inputs['Intensity'].default_value = 0.0 if mute else ch.intensity_value
    height_proc.inputs['Intensity'].default_value = ch.intensity_value

    if ch.enable_transition_bump and ch.enable and ch.transition_bump_crease and not ch.transition_bump_flip:
        height_proc.inputs['Crease Factor'].default_value = ch.transition_bump_crease_factor
        height_proc.inputs['Crease Power'].default_value = ch.transition_bump_crease_power

        if not ch.write_height and not root_ch.enable_smooth_bump:
            height_proc.inputs['Remaining Filter'].default_value = 1.0
        else: height_proc.inputs['Remaining Filter'].default_value = 0.0

    # Height Blend

    if ch.normal_blend_type in {'MIX', 'OVERLAY'}:

        if ch.normal_blend_type == 'MIX':

            if layer.parent_idx != -1:
                height_blend, need_reconnect = replace_new_node(
                        tree, ch, 'height_blend', 'ShaderNodeGroup', 'Height Blend', 
                        lib.STRAIGHT_OVER_HEIGHT_MIX, return_status=True, hard_replace=True, dirty=need_reconnect)
                if ch.write_height:
                    height_blend.inputs['Divide'].default_value = 1.0
                else: height_blend.inputs['Divide'].default_value = 0.0
            else:

                height_blend, need_reconnect = replace_new_node(
                        tree, ch, 'height_blend', 'ShaderNodeMixRGB', 'Height Blend', 
                        return_status=True, dirty=need_reconnect) #, hard_replace=True)

                height_blend.blend_type = 'MIX'

        elif ch.normal_blend_type == 'OVERLAY':

            if layer.parent_idx != -1:
                height_blend, need_reconnect = replace_new_node(
                        tree, ch, 'height_blend', 'ShaderNodeGroup', 'Height Blend', 
                        lib.STRAIGHT_OVER_HEIGHT_ADD, return_status=True, hard_replace=True, dirty=need_reconnect)
                if ch.write_height:
                    height_blend.inputs['Divide'].default_value = 1.0
                else: height_blend.inputs['Divide'].default_value = 0.0
            else:
                height_blend, need_reconnect = replace_new_node(
                        tree, ch, 'height_blend', 'ShaderNodeMixRGB', 'Height Blend', 
                        return_status=True, dirty=need_reconnect) #, hard_replace=True)

                height_blend.blend_type = 'ADD'

        if root_ch.enable_smooth_bump:
            for d in neighbor_directions:


                if ch.normal_blend_type == 'MIX':

                    if layer.parent_idx != -1:
                        hb, need_reconnect = replace_new_node(
                                tree, ch, 'height_blend_' + d, 'ShaderNodeGroup', 'Height Blend', 
                                lib.STRAIGHT_OVER_HEIGHT_MIX, return_status=True, hard_replace=True, dirty=need_reconnect)
                        if ch.write_height:
                            hb.inputs['Divide'].default_value = 1.0
                        else: hb.inputs['Divide'].default_value = 0.0
                    else:

                        hb, need_reconnect = replace_new_node(
                            tree, ch, 'height_blend_' + d, 'ShaderNodeMixRGB', 'Height Blend', 
                            return_status=True, dirty=need_reconnect) #, hard_replace=True)

                        hb.blend_type = 'MIX'

                elif ch.normal_blend_type == 'OVERLAY':

                    if layer.parent_idx != -1:
                        hb, need_reconnect = replace_new_node(
                                tree, ch, 'height_blend_' + d, 'ShaderNodeGroup', 'Height Blend', 
                                lib.STRAIGHT_OVER_HEIGHT_ADD, return_status=True, hard_replace=True, dirty=need_reconnect)
                        if ch.write_height:
                            hb.inputs['Divide'].default_value = 1.0
                        else: hb.inputs['Divide'].default_value = 0.0
                    else:

                        hb, need_reconnect = replace_new_node(
                            tree, ch, 'height_blend_' + d, 'ShaderNodeMixRGB', 'Height Blend', 
                            return_status=True, dirty=need_reconnect) #, hard_replace=True)

                        hb.blend_type = 'ADD'

    else:

        height_blend, need_reconnect = replace_new_node(
                tree, ch, 'height_blend', 'ShaderNodeGroup', 'Height Blend', 
                lib.HEIGHT_COMPARE, return_status=True, hard_replace=True, dirty=need_reconnect)

        if root_ch.enable_smooth_bump:
            for d in neighbor_directions:
                hb, need_reconnect = replace_new_node(
                    tree, ch, 'height_blend_' + d, 'ShaderNodeGroup', 'Height Blend', 
                    lib.HEIGHT_COMPARE, return_status=True, hard_replace=True, dirty=need_reconnect)

    if not root_ch.enable_smooth_bump:
        for d in neighbor_directions:
            remove_node(tree, ch, 'normal_flip_' + d)

    #if root_ch.enable_smooth_bump:
    #    if ch.normal_blend_type == 'MIX':
    #        lib_name = lib.HEIGHT_MIX_SMOOTH
    #    elif ch.normal_blend_type == 'OVERLAY':
    #        lib_name = lib.HEIGHT_ADD_SMOOTH
    #    else:
    #        lib_name = lib.HEIGHT_COMPARE_SMOOTH

    #    height_blend, need_reconnect = replace_new_node(
    #            tree, ch, 'height_blend', 'ShaderNodeGroup', 'Height Blend', 
    #            lib_name, return_status = True, hard_replace=True)
    #else:
    #    if ch.normal_blend_type == 'MIX':
    #        height_blend, need_reconnect = replace_new_node(
    #                tree, ch, 'height_blend', 'ShaderNodeMixRGB', 'Height Blend', 
    #                return_status = True, hard_replace=True)
    #        height_blend.blend_type = 'MIX'
    #    elif ch.normal_blend_type == 'OVERLAY':
    #        height_blend, need_reconnect = replace_new_node(
    #                tree, ch, 'height_blend', 'ShaderNodeMixRGB', 'Height Blend', 
    #                return_status = True, hard_replace=True)
    #        height_blend.blend_type = 'ADD'
    #    else:
    #        height_blend, need_reconnect = replace_new_node(
    #                tree, ch, 'height_blend', 'ShaderNodeGroup', 'Height Blend', 
    #                lib.HEIGHT_COMPARE, return_status = True, hard_replace=True)

    # Normal Process
    if ch.normal_map_type == 'NORMAL_MAP':
        if root_ch.enable_smooth_bump:
            if ch.enable_transition_bump:
                lib_name = lib.NORMAL_MAP_PROCESS_SMOOTH_TRANSITION
            else:
                lib_name = lib.NORMAL_MAP_PROCESS_SMOOTH
        else:
            if ch.enable_transition_bump:
                lib_name = lib.NORMAL_MAP_PROCESS_TRANSITION
            else:
                lib_name = lib.NORMAL_MAP_PROCESS
    else:
        if root_ch.enable_smooth_bump:
            lib_name = lib.NORMAL_PROCESS_SMOOTH
        else:
            lib_name = lib.NORMAL_PROCESS

        if layer.type == 'GROUP':
            lib_name += ' Group'

    normal_proc, need_reconnect = replace_new_node(
            tree, ch, 'normal_proc', 'ShaderNodeGroup', 'Normal Process', 
            lib_name, return_status = True, hard_replace=True, dirty=need_reconnect)

    normal_proc.inputs['Max Height'].default_value = max_height
    if root_ch.enable_smooth_bump:
        normal_proc.inputs['Bump Height Scale'].default_value = get_fine_bump_distance(max_height)

    if 'Intensity' in normal_proc.inputs:
        #normal_proc.inputs['Intensity'].default_value = 0.0 if mute else ch.intensity_value
        normal_proc.inputs['Intensity'].default_value = ch.intensity_value

    # Normal flip
    if ch.normal_map_type == 'NORMAL_MAP' or root_ch.enable_smooth_bump:
        remove_node(tree, ch, 'normal_flip')
    else:
        normal_flip = replace_new_node(tree, ch, 'normal_flip', 'ShaderNodeGroup', 
                'Normal Backface Flip', lib.FLIP_BACKFACE_BUMP)

        set_bump_backface_flip(normal_flip, yp.enable_backface_always_up)

    return need_reconnect

def remove_layer_channel_nodes(layer, ch, tree=None):
    if not tree: tree = get_tree(layer)

    remove_node(tree, ch, 'intensity')
    remove_node(tree, ch, 'blend')
    remove_node(tree, ch, 'extra_alpha')

def check_blend_type_nodes(root_ch, layer, ch):

    #print("Checking blend type nodes. Layer: " + layer.name + ' Channel: ' + root_ch.name)

    yp = layer.id_data.yp
    tree = get_tree(layer)
    nodes = tree.nodes
    blend = nodes.get(ch.blend)

    need_reconnect = False

    # Update normal map nodes
    if root_ch.type == 'NORMAL':
        need_reconnect = check_channel_normal_map_nodes(tree, layer, root_ch, ch, need_reconnect)

    # Extra alpha
    need_reconnect = check_extra_alpha(layer, need_reconnect)

    #if yp.disable_quick_toggle and not ch.enable:
    if not ch.enable:
        remove_layer_channel_nodes(layer, ch, tree)
        return need_reconnect

    has_parent = layer.parent_idx != -1

    # Background layer always using mix blend type
    if layer.type == 'BACKGROUND':
        blend_type = 'MIX'
    else: blend_type = ch.blend_type

    if root_ch.type == 'RGB':

        if (has_parent or root_ch.enable_alpha) and blend_type == 'MIX':

            if (layer.type == 'BACKGROUND' and not 
                    (ch.enable_transition_ramp and ch.transition_ramp_intensity_unlink 
                        and ch.transition_ramp_blend_type == 'MIX') and not 
                    (ch.enable_transition_ramp and layer.parent_idx != -1 and ch.transition_ramp_blend_type == 'MIX')
                    ):
                blend, need_reconnect = replace_new_node(tree, ch, 'blend', 
                        'ShaderNodeGroup', 'Blend', lib.STRAIGHT_OVER_BG, return_status = True, 
                        hard_replace=True, dirty=need_reconnect)

            else: 
                blend, need_reconnect = replace_new_node(tree, ch, 'blend', 
                        'ShaderNodeGroup', 'Blend', lib.STRAIGHT_OVER, 
                        return_status = True, hard_replace=True, dirty=need_reconnect)

        else:
            blend, need_reconnect = replace_new_node(tree, ch, 'blend', 
                    'ShaderNodeMixRGB', 'Blend', return_status = True, hard_replace=True, dirty=need_reconnect)

    elif root_ch.type == 'NORMAL':

        if has_parent and ch.normal_blend_type == 'MIX':
            if layer.type == 'BACKGROUND':
                blend, need_reconnect = replace_new_node(tree, ch, 'blend', 
                        'ShaderNodeGroup', 'Blend', lib.STRAIGHT_OVER_BG_VEC, 
                        return_status = True, hard_replace=True, dirty=need_reconnect)
            else:
                blend, need_reconnect = replace_new_node(tree, ch, 'blend', 
                        'ShaderNodeGroup', 'Blend', lib.STRAIGHT_OVER_VEC, 
                        return_status = True, hard_replace=True, dirty=need_reconnect)

        elif ch.normal_blend_type == 'OVERLAY':
            if has_parent:
                blend, need_reconnect = replace_new_node(tree, ch, 'blend', 
                        'ShaderNodeGroup', 'Blend', lib.OVERLAY_NORMAL_STRAIGHT_OVER, 
                        return_status = True, hard_replace=True, dirty=need_reconnect)
            else:
                blend, need_reconnect = replace_new_node(tree, ch, 'blend', 
                        'ShaderNodeGroup', 'Blend', lib.OVERLAY_NORMAL, 
                        return_status = True, hard_replace=True, dirty=need_reconnect)

        elif ch.normal_blend_type == 'MIX':
            blend, need_reconnect = replace_new_node(tree, ch, 'blend', 
                    'ShaderNodeGroup', 'Blend', lib.VECTOR_MIX, 
                    return_status = True, hard_replace=True, dirty=need_reconnect)

        if not root_ch.enable_smooth_bump:
            for d in neighbor_directions:
                remove_node(tree, ch, 'height_blend_' + d)

    elif root_ch.type == 'VALUE':

        if has_parent and blend_type == 'MIX':
            if layer.type == 'BACKGROUND':
                blend, need_reconnect = replace_new_node(tree, ch, 'blend', 
                        'ShaderNodeGroup', 'Blend', lib.STRAIGHT_OVER_BG_BW, 
                        return_status = True, hard_replace=True, dirty=need_reconnect)
            else:
                blend, need_reconnect = replace_new_node(tree, ch, 'blend', 
                        'ShaderNodeGroup', 'Blend', lib.STRAIGHT_OVER_BW, 
                        return_status = True, hard_replace=True, dirty=need_reconnect)
        else:

            blend, need_reconnect = replace_new_node(tree, ch, 'blend', 
                    'ShaderNodeMixRGB', 'Blend', return_status = True, hard_replace=True, dirty=need_reconnect)

    if root_ch.type != 'NORMAL' and blend.type == 'MIX_RGB' and blend.blend_type != blend_type:
        blend.blend_type = blend_type

    # Mute
    #mute = not layer.enable or not ch.enable
    #if yp.disable_quick_toggle:
    #    blend.mute = mute
    #else: blend.mute = False
    #blend.mute = mute

    # Intensity nodes
    if root_ch.type == 'NORMAL':
        remove_node(tree, ch, 'intensity')
    else:
        intensity = tree.nodes.get(ch.intensity)
        if not intensity:
            intensity = new_node(tree, ch, 'intensity', 'ShaderNodeMath', 'Intensity')
            intensity.operation = 'MULTIPLY'

        # Channel mute
        #intensity.inputs[1].default_value = 0.0 if mute else ch.intensity_value
        intensity.inputs[1].default_value = ch.intensity_value

    return need_reconnect

def check_extra_alpha(layer, need_reconnect=False):

    disp_ch = get_height_channel(layer)
    if not disp_ch: return

    tree = get_tree(layer)

    for ch in layer.channels:
        if disp_ch == ch: continue

        extra_alpha = tree.nodes.get(ch.extra_alpha)

        if disp_ch.enable and disp_ch.normal_blend_type == 'COMPARE':

            if not extra_alpha:
                extra_alpha = new_node(tree, ch, 'extra_alpha', 'ShaderNodeMath', 'Extra Alpha')
                extra_alpha.operation = 'MULTIPLY'
                need_reconnect = True

        elif extra_alpha:
            remove_node(tree, ch, 'extra_alpha')
            need_reconnect = True

    return need_reconnect
    
def check_layer_image_linear_node(layer, source_tree=None):

    if not source_tree: source_tree = get_source_tree(layer)

    if layer.type == 'IMAGE':

        source = source_tree.nodes.get(layer.source)
        image = source.image

        # Create linear if image type is srgb
        if image.colorspace_settings.name == 'sRGB':
            linear = source_tree.nodes.get(layer.linear)
            if not linear:
                #linear = new_node(source_tree, layer, 'linear', 'ShaderNodeGamma', 'Linear')
                linear = new_node(source_tree, layer, 'linear', 'ShaderNodeGroup', 'Linear')
                linear.node_tree = get_node_tree_lib(lib.LINEAR_2_SRGB)

            return

    # Delete linear
    remove_node(source_tree, layer, 'linear')

def check_mask_image_linear_node(mask, mask_tree=None):

    if not mask_tree: mask_tree = get_mask_tree(mask)

    if mask.type == 'IMAGE':

        source = mask_tree.nodes.get(mask.source)
        image = source.image

        # Create linear if image type is srgb
        if image.colorspace_settings.name == 'sRGB':
            linear = mask_tree.nodes.get(mask.linear)
            if not linear:
                #linear = new_node(mask_tree, mask, 'linear', 'ShaderNodeGamma', 'Linear')
                linear = new_node(mask_tree, mask, 'linear', 'ShaderNodeGroup', 'Linear')
                linear.node_tree = get_node_tree_lib(lib.LINEAR_2_SRGB)

            return

    # Delete linear
    remove_node(mask_tree, mask, 'linear')
