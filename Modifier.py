import bpy, re
from bpy.props import *
from .common import *
from .subtree import *
from .node_connections import *
from .node_arrangements import *
from . import lib

modifier_type_items = (
        ('INVERT', 'Invert', 
            'Invert input RGB and/or Alpha', 'MODIFIER', 0),

        ('RGB_TO_INTENSITY', 'RGB to Intensity',
            'Input RGB will be used as alpha output, Output RGB will be replaced using custom color.', 
            'MODIFIER', 1),

        ('INTENSITY_TO_RGB', 'Intensity to RGB',
            'Input alpha will be used as RGB output, Output Alpha will use solid value of one.', 
            'MODIFIER', 2),

        # Deprecated
        ('OVERRIDE_COLOR', 'Override Color',
            'Input RGB will be replaced with custom RGB', 
            'MODIFIER', 3),

        ('COLOR_RAMP', 'Color Ramp', '', 'MODIFIER', 4),
        ('RGB_CURVE', 'RGB Curve', '', 'MODIFIER', 5),
        ('HUE_SATURATION', 'Hue Saturation', '', 'MODIFIER', 6),
        ('BRIGHT_CONTRAST', 'Brightness Contrast', '', 'MODIFIER', 7),
        # Deprecated
        ('MULTIPLIER', 'Multiplier', '', 'MODIFIER', 8),
        ('MATH', 'Math', '', 'MODIFIER',9)
        )

can_be_expanded = {
        'INVERT', 
        'RGB_TO_INTENSITY', 
        'OVERRIDE_COLOR', # Deprecated
        'COLOR_RAMP',
        'RGB_CURVE',
        'HUE_SATURATION',
        'BRIGHT_CONTRAST',
        'MULTIPLIER', # Deprecated
        'MATH'
        }

def get_modifier_channel_type(mod, return_non_color=False):

    yp = mod.id_data.yp
    match1 = re.match(r'yp\.layers\[(\d+)\]\.channels\[(\d+)\]\.modifiers\[(\d+)\]', mod.path_from_id())
    match2 = re.match(r'yp\.channels\[(\d+)\]\.modifiers\[(\d+)\]', mod.path_from_id())
    match3 = re.match(r'yp\.layers\[(\d+)\]\.modifiers\[(\d+)\]', mod.path_from_id())
    if match1: 
        root_ch = yp.channels[int(match1.group(2))]

        # Get non color flag and channel type
        non_color = root_ch.colorspace == 'LINEAR'
        channel_type = root_ch.type
    elif match2:
        root_ch = yp.channels[int(match2.group(1))]

        # Get non color flag and channel type
        non_color = root_ch.colorspace == 'LINEAR'
        channel_type = root_ch.type
    elif match3:

        # Image layer modifiers always use srgb colorspace
        layer = yp.layers[int(match3.group(1))]
        non_color = layer.type != 'IMAGE'
        channel_type = 'RGB'

    if return_non_color:
        return channel_type, non_color

    return channel_type

def check_modifier_nodes(m, tree, ref_tree=None):

    yp = m.id_data.yp
    nodes = tree.nodes

    # Get channel type and non color status
    channel_type, non_color = get_modifier_channel_type(m, True)

    # Pipeline nodes
    #if not m.enable:
    #    remove_node(tree, m, 'frame')
    #else:
    #    frame, frame_dirty = check_new_node(tree, m, 'frame', 'NodeFrame', '', True)
    #remove_node(tree, m, 'frame')

    # Check the nodes
    if m.type == 'INVERT':

        if not m.enable:
            remove_node(tree, m, 'invert')
        else:
            if ref_tree:
                invert_ref = ref_tree.nodes.get(m.invert)
                ref_tree.nodes.remove(invert_ref)

                invert = new_node(tree, m, 'invert', 'ShaderNodeGroup', 'Invert')
                dirty = True
            else:
                invert, dirty = check_new_node(tree, m, 'invert', 'ShaderNodeGroup', 'Invert', True)

            if dirty:
                if channel_type == 'VALUE':
                    invert.node_tree = get_node_tree_lib(lib.MOD_INVERT_VALUE)
                else: invert.node_tree = get_node_tree_lib(lib.MOD_INVERT)

                invert.inputs[2].default_value = 1.0 if m.invert_r_enable else 0.0
                if channel_type == 'VALUE':
                    invert.inputs[3].default_value = 1.0 if m.invert_a_enable else 0.0
                else:
                    invert.inputs[3].default_value = 1.0 if m.invert_g_enable else 0.0
                    invert.inputs[4].default_value = 1.0 if m.invert_b_enable else 0.0
                    invert.inputs[5].default_value = 1.0 if m.invert_a_enable else 0.0

            #if frame_dirty:
            #    frame.label = 'Invert'
            #    invert.parent = frame

    elif m.type == 'RGB_TO_INTENSITY':

        if not m.enable:
            remove_node(tree, m, 'rgb2i')
        else:
            if ref_tree:
                rgb2i_ref = ref_tree.nodes.get(m.rgb2i)
                ref_tree.nodes.remove(rgb2i_ref)

                rgb2i = new_node(tree, m, 'rgb2i', 'ShaderNodeGroup', 'RGB to Intensity')
                dirty = True
            else:
                rgb2i, dirty = check_new_node(tree, m, 'rgb2i', 'ShaderNodeGroup', 'RGB to Intensity', True)

            if dirty:
                rgb2i.node_tree = get_node_tree_lib(lib.MOD_RGB2INT)

                rgb2i.inputs['RGB To Intensity Color'].default_value = m.rgb2i_col
                if non_color:
                    rgb2i.inputs['Gamma'].default_value = 1.0
                else: rgb2i.inputs['Gamma'].default_value = 1.0/GAMMA

            #if frame_dirty:
            #    frame.label = 'RGB to Intensity'
            #    rgb2i.parent = frame

    elif m.type == 'INTENSITY_TO_RGB':

        if not m.enable:
            remove_node(tree, m, 'i2rgb')
        else:
            if ref_tree:
                i2rgb_ref = ref_tree.nodes.get(m.i2rgb)
                ref_tree.nodes.remove(i2rgb_ref)

                i2rgb = new_node(tree, m, 'i2rgb', 'ShaderNodeGroup', 'Intensity to RGB')
                dirty = True
            else:
                i2rgb, dirty = check_new_node(tree, m, 'i2rgb', 'ShaderNodeGroup', 'Intensity to RGB', True)

            if dirty:
                i2rgb.node_tree = get_node_tree_lib(lib.MOD_INT2RGB)

            #if frame_dirty:
            #    frame.label = 'Intensity to RGB'
            #    i2rgb.parent = frame

    elif m.type == 'OVERRIDE_COLOR':

        if not m.enable:
            remove_node(tree, m, 'oc')
        else:
            if ref_tree:
                oc_ref = ref_tree.nodes.get(m.oc)
                ref_tree.nodes.remove(oc_ref)

                oc = new_node(tree, m, 'oc', 'ShaderNodeGroup', 'Override Color')
                dirty = True
            else:
                oc, dirty = check_new_node(tree, m, 'oc', 'ShaderNodeGroup', 'Override Color', True)

            if dirty:
                oc.node_tree = get_node_tree_lib(lib.MOD_OVERRIDE_COLOR)

                if channel_type == 'VALUE':
                    col = (m.oc_val, m.oc_val, m.oc_val, 1.0)
                else: col = m.oc_col
                oc.inputs['Override Color'].default_value = col

                if non_color:
                    oc.inputs['Gamma'].default_value = 1.0
                else: oc.inputs['Gamma'].default_value = 1.0/GAMMA

            #if frame_dirty:
            #    frame.label = 'Override Color'
            #    oc.parent = frame

    elif m.type == 'COLOR_RAMP':

        if not m.enable:

            if ref_tree:
                color_ramp_ref = ref_tree.nodes.get(m.color_ramp)
                if color_ramp_ref:
                    color_ramp = new_node(tree, m, 'color_ramp', 'ShaderNodeValToRGB', 'ColorRamp')
                    copy_node_props(color_ramp_ref, color_ramp)
                    ref_tree.nodes.remove(color_ramp_ref)

            remove_node(tree, m, 'color_ramp_linear_start')
            remove_node(tree, m, 'color_ramp_linear')
            remove_node(tree, m, 'color_ramp_alpha_multiply')
            remove_node(tree, m, 'color_ramp_mix_rgb')
            remove_node(tree, m, 'color_ramp_mix_alpha')
        else:
            if ref_tree:
                color_ramp_alpha_multiply_ref = ref_tree.nodes.get(m.color_ramp_alpha_multiply)
                color_ramp_linear_start_ref = ref_tree.nodes.get(m.color_ramp_linear_start)
                color_ramp_ref = ref_tree.nodes.get(m.color_ramp)
                color_ramp_linear_ref = ref_tree.nodes.get(m.color_ramp_linear)
                color_ramp_mix_alpha_ref = ref_tree.nodes.get(m.color_ramp_mix_alpha)
                color_ramp_mix_rgb_ref = ref_tree.nodes.get(m.color_ramp_mix_rgb)

                # Create new nodes if reference is used
                color_ramp_alpha_multiply = new_mix_node(tree, m, 'color_ramp_alpha_multiply', 'ColorRamp Alpha Multiply')
                color_ramp_linear_start = new_node(tree, m, 'color_ramp_linear_start', 'ShaderNodeGamma', 'ColorRamp Linear Start')
                color_ramp = new_node(tree, m, 'color_ramp', 'ShaderNodeValToRGB', 'ColorRamp')
                color_ramp_linear = new_node(tree, m, 'color_ramp_linear', 'ShaderNodeGamma', 'ColorRamp Linear')
                color_ramp_mix_alpha = new_mix_node(tree, m, 'color_ramp_mix_alpha', 'ColorRamp Mix Alpha')
                color_ramp_mix_rgb = new_mix_node(tree, m, 'color_ramp_mix_rgb', 'ColorRamp Mix RGB')
                dirty = True
                ramp_dirty = False
            else:

                color_ramp_alpha_multiply, dirty = check_new_mix_node(tree, m, 'color_ramp_alpha_multiply', 'ColorRamp Alpha Multiply', True)
                color_ramp_linear_start = check_new_node(tree, m, 'color_ramp_linear_start', 'ShaderNodeGamma', 'ColorRamp Linear Start')
                color_ramp, ramp_dirty = check_new_node(tree, m, 'color_ramp', 'ShaderNodeValToRGB', 'ColorRamp', True)
                color_ramp_linear = check_new_node(tree, m, 'color_ramp_linear', 'ShaderNodeGamma', 'ColorRamp Linear')
                color_ramp_mix_alpha = check_new_mix_node(tree, m, 'color_ramp_mix_alpha', 'ColorRamp Mix Alpha')
                color_ramp_mix_rgb = check_new_mix_node(tree, m, 'color_ramp_mix_rgb', 'ColorRamp Mix RGB')

            if ref_tree:
                copy_node_props(color_ramp_alpha_multiply_ref, color_ramp_alpha_multiply)
                if color_ramp_linear_start_ref: copy_node_props(color_ramp_linear_start_ref, color_ramp_linear_start)
                copy_node_props(color_ramp_ref, color_ramp)
                copy_node_props(color_ramp_linear_ref, color_ramp_linear)
                copy_node_props(color_ramp_mix_alpha_ref, color_ramp_mix_alpha)
                copy_node_props(color_ramp_mix_rgb_ref, color_ramp_mix_rgb)

                ref_tree.nodes.remove(color_ramp_alpha_multiply_ref)
                if color_ramp_linear_start_ref: ref_tree.nodes.remove(color_ramp_linear_start_ref)
                ref_tree.nodes.remove(color_ramp_ref)
                ref_tree.nodes.remove(color_ramp_linear_ref)
                ref_tree.nodes.remove(color_ramp_mix_alpha_ref)
                ref_tree.nodes.remove(color_ramp_mix_rgb_ref)

            elif dirty:

                color_ramp_alpha_multiply.inputs[0].default_value = 1.0
                color_ramp_alpha_multiply.blend_type = 'MULTIPLY'
                color_ramp_mix_alpha.inputs[0].default_value = 1.0
                color_ramp_mix_rgb.inputs[0].default_value = 1.0

            if non_color:
                color_ramp_linear_start.inputs[1].default_value = 1.0
                color_ramp_linear.inputs[1].default_value = 1.0
            else: 
                color_ramp_linear_start.inputs[1].default_value = GAMMA
                color_ramp_linear.inputs[1].default_value = 1.0/GAMMA

            if ramp_dirty:
                # Set default color if ramp just created
                color_ramp.color_ramp.elements[0].color = (0,0,0,0) 

            #if frame_dirty:
            #    frame.label = 'Color Ramp'
            #    color_ramp.parent = frame
            #    color_ramp_linear.parent = frame
            #    color_ramp_alpha_multiply.parent = frame
            #    color_ramp_mix_alpha.parent = frame
            #    color_ramp_mix_rgb.parent = frame

    elif m.type == 'RGB_CURVE':

        if ref_tree:
            rgb_curve_ref = ref_tree.nodes.get(m.rgb_curve)
            rgb_curve = new_node(tree, m, 'rgb_curve', 'ShaderNodeRGBCurve', 'RGB Curve')
            if rgb_curve_ref:
                # Copy from reference
                copy_node_props(rgb_curve_ref, rgb_curve)
                ref_tree.nodes.remove(rgb_curve_ref)
        else:
            rgb_curve = check_new_node(tree, m, 'rgb_curve', 'ShaderNodeRGBCurve', 'RGB Curve')

        #if frame_dirty:
        #    frame.label = 'RGB Curve'
        #    rgb_curve.parent = frame

    elif m.type == 'HUE_SATURATION':

        if not m.enable:
            remove_node(tree, m, 'huesat')
        else:
            if ref_tree:
                # Remove previous nodes
                huesat_ref = ref_tree.nodes.get(m.huesat)
                ref_tree.nodes.remove(huesat_ref)

                huesat = new_node(tree, m, 'huesat', 'ShaderNodeHueSaturation', 'Hue Saturation')
                dirty = True
            else:
                huesat, dirty = check_new_node(tree, m, 'huesat', 'ShaderNodeHueSaturation', 'Hue Saturation', True)

            if dirty:
                huesat.inputs['Hue'].default_value = m.huesat_hue_val
                huesat.inputs['Saturation'].default_value = m.huesat_saturation_val
                huesat.inputs['Value'].default_value = m.huesat_value_val

            #if frame_dirty:
            #    frame.label = 'Hue Saturation Value'
            #    huesat.parent = frame

    elif m.type == 'BRIGHT_CONTRAST':

        if not m.enable:
            remove_node(tree, m, 'brightcon')
        else:
            if ref_tree:
                # Remove previous nodes
                brightcon_ref = ref_tree.nodes.get(m.brightcon)
                ref_tree.nodes.remove(brightcon_ref)

                brightcon = new_node(tree, m, 'brightcon', 'ShaderNodeBrightContrast', 'Brightness Contrast')
                dirty = True
            else:
                brightcon, dirty = check_new_node(tree, m, 'brightcon', 'ShaderNodeBrightContrast', 'Brightness Contrast', True)

            if dirty:
                brightcon.inputs['Bright'].default_value = m.brightness_value
                brightcon.inputs['Contrast'].default_value = m.contrast_value

            #if frame_dirty:
            #    frame.label = 'Brightness Contrast'
            #    brightcon.parent = frame

    elif m.type == 'MULTIPLIER':

        if not m.enable:
            remove_node(tree, m, 'multiplier')
        else:
            if ref_tree:
                # Remove previous nodes
                multiplier_ref = ref_tree.nodes.get(m.multiplier)
                ref_tree.nodes.remove(multiplier_ref)

                multiplier = new_node(tree, m, 'multiplier', 'ShaderNodeGroup', 'Multiplier')
                dirty = True
            else:
                multiplier, dirty = check_new_node(tree, m, 'multiplier', 'ShaderNodeGroup', 'Multiplier', True)

            if dirty:
                if channel_type == 'VALUE':
                    multiplier.node_tree = get_node_tree_lib(lib.MOD_MULTIPLIER_VALUE)
                else: multiplier.node_tree = get_node_tree_lib(lib.MOD_MULTIPLIER)

                multiplier.inputs[2].default_value = 1.0 if m.use_clamp else 0.0
                multiplier.inputs[3].default_value = m.multiplier_r_val
                if channel_type == 'VALUE':
                    multiplier.inputs[4].default_value = m.multiplier_a_val
                else:
                    multiplier.inputs[4].default_value = m.multiplier_g_val
                    multiplier.inputs[5].default_value = m.multiplier_b_val
                    multiplier.inputs[6].default_value = m.multiplier_a_val

            #if frame_dirty:
            #    frame.label = 'Multiplier'
            #    multiplier.parent = frame

    elif m.type == 'MATH':

        if not m.enable:
            remove_node(tree, m, 'math')
        else:
            if ref_tree:
                # Remove previous nodes
                math_ref = ref_tree.nodes.get(m.math)
                ref_tree.nodes.remove(math_ref)

                math = new_node(tree, m, 'math', 'ShaderNodeGroup', 'Math')
                dirty = True
            else:
                math, dirty = check_new_node(tree, m, 'math', 'ShaderNodeGroup', 'Math', True)

            if dirty:
                if channel_type == 'VALUE':
                    math.node_tree = get_node_tree_lib(lib.MOD_MATH_VALUE)
                else :
                    math.node_tree = get_node_tree_lib(lib.MOD_MATH)

                duplicate_lib_node_tree(math)
                math.inputs[2].default_value = m.math_r_val

                math.node_tree.nodes.get('Math.R').operation = m.math_meth
                math.node_tree.nodes.get('Math.A').operation = m.math_meth

                math.node_tree.nodes.get('Math.R').use_clamp = m.use_clamp
                math.node_tree.nodes.get('Math.A').use_clamp = m.use_clamp

                if channel_type == 'VALUE':
                    math.inputs[3].default_value = m.math_a_val
                else:
                    math.inputs[3].default_value = m.math_g_val
                    math.inputs[4].default_value = m.math_b_val
                    math.inputs[5].default_value = m.math_a_val

                    math.node_tree.nodes.get('Math.G').operation = m.math_meth
                    math.node_tree.nodes.get('Math.B').operation = m.math_meth

                    math.node_tree.nodes.get('Math.G').use_clamp = m.use_clamp
                    math.node_tree.nodes.get('Math.B').use_clamp = m.use_clamp

def add_new_modifier(parent, modifier_type):

    yp = parent.id_data.yp

    match1 = re.match(r'^yp\.layers\[(\d+)\]\.channels\[(\d+)\]$', parent.path_from_id())
    match2 = re.match(r'^yp\.layers\[(\d+)\]$', parent.path_from_id())
    match3 = re.match(r'^yp\.channels\[(\d+)\]$', parent.path_from_id())

    if match1: 
        root_ch = yp.channels[int(match1.group(2))]
        channel_type = root_ch.type
    elif match3:
        root_ch = yp.channels[int(match3.group(1))]
        channel_type = root_ch.type
    elif match2:
        channel_type = 'RGB'
    
    tree = get_mod_tree(parent)
    modifiers = parent.modifiers

    # Add new modifier and move it to the top
    m = modifiers.add()

    if channel_type == 'VALUE' and modifier_type == 'OVERRIDE_COLOR':
        name = 'Override Value'
    else: name = [mt[1] for mt in modifier_type_items if mt[0] == modifier_type][0]

    m.name = get_unique_name(name, modifiers)
    modifiers.move(len(modifiers)-1, 0)
    shift_modifier_fcurves_down(parent)
    m = modifiers[0]
    m.type = modifier_type
    #m.channel_type = root_ch.type

    check_modifier_nodes(m, tree)

    if match1: 
        # Enable modifier tree if fine bump map is used
        if root_ch.type == 'NORMAL' and root_ch.enable_smooth_bump:
        #if parent.normal_map_type == 'FINE_BUMP_MAP' or (
        #        parent.enable_transition_bump and parent.transition_bump_type in {'FINE_BUMP_MAP', 'CURVED_BUMP_MAP'}):
            enable_modifiers_tree(parent)
    elif match2 and parent.type not in {'IMAGE', 'VCOL', 'BACKGROUND'}:
        enable_modifiers_tree(parent)

    return m

def delete_modifier_nodes(tree, mod):

    # Delete the nodes
    remove_node(tree, mod, 'frame')

    if mod.type == 'RGB_TO_INTENSITY':
        remove_node(tree, mod, 'rgb2i')

    elif mod.type == 'INTENSITY_TO_RGB':
        remove_node(tree, mod, 'i2rgb')

    elif mod.type == 'OVERRIDE_COLOR':
        remove_node(tree, mod, 'oc')

    elif mod.type == 'INVERT':
        remove_node(tree, mod, 'invert')

    elif mod.type == 'COLOR_RAMP':
        remove_node(tree, mod, 'color_ramp_linear_start')
        remove_node(tree, mod, 'color_ramp')
        remove_node(tree, mod, 'color_ramp_linear')
        remove_node(tree, mod, 'color_ramp_alpha_multiply')
        remove_node(tree, mod, 'color_ramp_mix_rgb')
        remove_node(tree, mod, 'color_ramp_mix_alpha')

    elif mod.type == 'RGB_CURVE':
        remove_node(tree, mod, 'rgb_curve')

    elif mod.type == 'HUE_SATURATION':
        remove_node(tree, mod, 'huesat')

    elif mod.type == 'BRIGHT_CONTRAST':
        remove_node(tree, mod, 'brightcon')

    elif mod.type == 'MULTIPLIER':
        remove_node(tree, mod, 'multiplier')

    elif mod.type == 'MATH':
        remove_node(tree, mod, 'math')

class YNewYPaintModifier(bpy.types.Operator):
    bl_idname = "node.y_new_ypaint_modifier"
    bl_label = "New " + get_addon_title() + " Modifier"
    bl_description = "New " + get_addon_title() + " Modifier"
    bl_options = {'REGISTER', 'UNDO'}

    type : EnumProperty(
        name = 'Modifier Type',
        items = modifier_type_items,
        default = 'INVERT')

    @classmethod
    def poll(cls, context):
        return get_active_ypaint_node() and hasattr(context, 'parent')

    def execute(self, context):
        node = get_active_ypaint_node()
        group_tree = node.node_tree
        yp = group_tree.yp

        m1 = re.match(r'^yp\.layers\[(\d+)\]$', context.parent.path_from_id())
        m2 = re.match(r'^yp\.layers\[(\d+)\]\.channels\[(\d+)\]$', context.parent.path_from_id())
        m3 = re.match(r'^yp\.channels\[(\d+)\]$', context.parent.path_from_id())

        if m1: layer = yp.layers[int(m1.group(1))]
        elif m2: layer = yp.layers[int(m2.group(1))]
        else: layer = None

        mod = add_new_modifier(context.parent, self.type)

        #if self.type == 'RGB_TO_INTENSITY' and root_ch.type == 'RGB':
        #    mod.rgb2i_col = (1,0,1,1)

        # If RGB to intensity is added, bump base is better be 0.0
        if layer and self.type == 'RGB_TO_INTENSITY':
            for i, ch in enumerate(yp.channels):
                c = context.layer.channels[i]
                if ch.type == 'NORMAL':
                    c.bump_base_value = 0.0

        # Expand channel content to see added modifier
        if m1:
            context.layer_ui.expand_content = True
        elif m2:
            context.layer_ui.channels[int(m2.group(2))].expand_content = True
        elif m3:
            context.channel_ui.expand_content = True

        # Rearrange nodes
        if layer:
            rearrange_layer_nodes(layer)
            reconnect_layer_nodes(layer)
        else: 
            rearrange_yp_nodes(group_tree)
            reconnect_yp_nodes(group_tree)

        # Reconnect modifier nodes
        #reconnect_between_modifier_nodes(context.parent)

        # Update UI
        context.window_manager.ypui.need_update = True

        return {'FINISHED'}

class YMoveYPaintModifier(bpy.types.Operator):
    bl_idname = "node.y_move_ypaint_modifier"
    bl_label = "Move " + get_addon_title() + " Modifier"
    bl_description = "Move " + get_addon_title() + " Modifier"
    bl_options = {'REGISTER', 'UNDO'}

    direction : EnumProperty(
            name = 'Direction',
            items = (('UP', 'Up', ''),
                     ('DOWN', 'Down', '')),
            default = 'UP')

    @classmethod
    def poll(cls, context):
        return (get_active_ypaint_node() and 
                hasattr(context, 'parent') and hasattr(context, 'modifier'))

    def execute(self, context):
        node = get_active_ypaint_node()
        group_tree = node.node_tree
        yp = group_tree.yp

        parent = context.parent

        num_mods = len(parent.modifiers)
        if num_mods < 2: return {'CANCELLED'}

        mod = context.modifier
        index = -1
        for i, m in enumerate(parent.modifiers):
            if m == mod:
                index = i
                break
        if index == -1: return {'CANCELLED'}

        # Get new index
        if self.direction == 'UP' and index > 0:
            new_index = index-1
        elif self.direction == 'DOWN' and index < num_mods-1:
            new_index = index+1
        else:
            return {'CANCELLED'}

        layer = context.layer if hasattr(context, 'layer') else None

        #if layer: tree = get_tree(layer)
        #else: tree = group_tree

        # Swap modifier
        parent.modifiers.move(index, new_index)
        swap_modifier_fcurves(parent, index, new_index)

        # Reconnect modifier nodes
        #reconnect_between_modifier_nodes(parent)

        # Rearrange nodes
        if layer: 
            reconnect_layer_nodes(layer)
            rearrange_layer_nodes(layer)
        else: 
            reconnect_yp_nodes(group_tree)
            rearrange_yp_nodes(group_tree)

        # Update UI
        context.window_manager.ypui.need_update = True

        return {'FINISHED'}

class YRemoveYPaintModifier(bpy.types.Operator):
    bl_idname = "node.y_remove_ypaint_modifier"
    bl_label = "Remove " + get_addon_title() + " Modifier"
    bl_description = "Remove " + get_addon_title() + " Modifier"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return hasattr(context, 'parent') and hasattr(context, 'modifier')

    def execute(self, context):
        group_tree = context.parent.id_data
        yp = group_tree.yp

        parent = context.parent
        mod = context.modifier

        index = -1
        for i, m in enumerate(parent.modifiers):
            if m == mod:
                index = i
                break
        if index == -1: return {'CANCELLED'}

        if len(parent.modifiers) < 1: return {'CANCELLED'}

        layer = context.layer if hasattr(context, 'layer') else None

        tree = get_mod_tree(parent)

        # Remove modifier fcurves first
        remove_entity_fcurves(mod)
        shift_modifier_fcurves_up(parent, index)

        # Delete the nodes
        delete_modifier_nodes(tree, mod)

        # Delete the modifier
        parent.modifiers.remove(index)

        # Delete modifier pipeline if no modifier left
        #if len(parent.modifiers) == 0:
        #    unset_modifier_pipeline_nodes(tree, parent)

        if layer:
            if len(parent.modifiers) == 0:
                disable_modifiers_tree(parent, False)
            reconnect_layer_nodes(layer)
        else:
            # Reconnect nodes
            #reconnect_between_modifier_nodes(parent)
            reconnect_yp_nodes(group_tree)

        # Rearrange nodes
        if layer:
            rearrange_layer_nodes(layer)
        else: rearrange_yp_nodes(group_tree)

        # Update UI
        context.window_manager.ypui.need_update = True

        return {'FINISHED'}

def draw_modifier_properties(context, channel_type, nodes, modifier, layout, is_layer_ch=False):

    if modifier.type == 'INVERT':
        row = layout.row(align=True)
        if channel_type == 'VALUE':
            row.prop(modifier, 'invert_r_enable', text='Value', toggle=True)
            row.prop(modifier, 'invert_a_enable', text='Alpha', toggle=True)
        else:
            row.prop(modifier, 'invert_r_enable', text='R', toggle=True)
            row.prop(modifier, 'invert_g_enable', text='G', toggle=True)
            row.prop(modifier, 'invert_b_enable', text='B', toggle=True)
            row.prop(modifier, 'invert_a_enable', text='A', toggle=True)

    elif modifier.type == 'RGB_TO_INTENSITY':
        col = layout.column(align=True)
        row = col.row()
        row.label(text='Color:')
        row.prop(modifier, 'rgb2i_col', text='')

        # Shortcut only available on layer channel
        #if 'YLayerChannel' in str(type(channel)):
        if is_layer_ch:
            row = col.row(align=True)
            row.label(text='Shortcut on layer list:')
            row.prop(modifier, 'shortcut', text='')

    elif modifier.type == 'OVERRIDE_COLOR':
        col = layout.column(align=True)

        row = col.row()
        if channel_type == 'VALUE':
            row.label(text='Value:')
            row.prop(modifier, 'oc_val', text='')
        else:
            row.label(text='Color:')
            row.prop(modifier, 'oc_col', text='')

            row = col.row()
            row.label(text='Shortcut on layer list:')
            row.prop(modifier, 'shortcut', text='')

    elif modifier.type == 'COLOR_RAMP':
        color_ramp = nodes.get(modifier.color_ramp)
        if color_ramp:
            layout.template_color_ramp(color_ramp, "color_ramp", expand=True)

    elif modifier.type == 'RGB_CURVE':
        rgb_curve = nodes.get(modifier.rgb_curve)
        if rgb_curve:
            rgb_curve.draw_buttons_ext(context, layout)

    elif modifier.type == 'HUE_SATURATION':
        row = layout.row(align=True)
        col = row.column(align=True)
        col.label(text='Hue:')
        col.label(text='Saturation:')
        col.label(text='Value:')

        col = row.column(align=True)
        col.prop(modifier, 'huesat_hue_val', text='')
        col.prop(modifier, 'huesat_saturation_val', text='')
        col.prop(modifier, 'huesat_value_val', text='')

    elif modifier.type == 'BRIGHT_CONTRAST':
        row = layout.row(align=True)
        col = row.column(align=True)
        col.label(text='Brightness:')
        col.label(text='Contrast:')

        col = row.column(align=True)
        col.prop(modifier, 'brightness_value', text='')
        col.prop(modifier, 'contrast_value', text='')

    elif modifier.type == 'MULTIPLIER':
        col = layout.column(align=True)
        row = col.row()
        row.label(text='Clamp:')
        row.prop(modifier, 'use_clamp', text='')
        if channel_type == 'VALUE':
            col.prop(modifier, 'multiplier_r_val', text='Value')
            col.prop(modifier, 'multiplier_a_val', text='Alpha')
        else:
            col.prop(modifier, 'multiplier_r_val', text='R')
            col.prop(modifier, 'multiplier_g_val', text='G')
            col.prop(modifier, 'multiplier_b_val', text='B')
            col.separator()
            col.prop(modifier, 'multiplier_a_val', text='Alpha')
    
    elif modifier.type == 'MATH':
        col = layout.column(align=True)
        row = col.row()
        col.prop(modifier, 'math_meth')
        row = col.row()
        row.label(text='Clamp:')
        row.prop(modifier, 'use_clamp', text='')
        if channel_type == 'VALUE':
            col.prop(modifier, 'math_r_val', text='Value')
        else :
            col.prop(modifier, 'math_r_val', text='R')
            col.prop(modifier, 'math_g_val', text='G')
            col.prop(modifier, 'math_b_val', text='B')
        col.separator()
        row = col.row()
        row.label(text='Affect Alpha:')
        row.prop(modifier, 'affect_alpha', text='')
        if modifier.affect_alpha :
            col.prop(modifier, 'math_a_val', text='A')

def update_modifier_enable(self, context):

    yp = self.id_data.yp
    if yp.halt_update: return
    tree = get_mod_tree(self)

    check_modifier_nodes(self, tree)

    match1 = re.match(r'yp\.layers\[(\d+)\]\.channels\[(\d+)\]\.modifiers\[(\d+)\]', self.path_from_id())
    match2 = re.match(r'yp\.layers\[(\d+)\]\.modifiers\[(\d+)\]', self.path_from_id())
    match3 = re.match(r'yp\.channels\[(\d+)\]\.modifiers\[(\d+)\]', self.path_from_id())

    if match1 or match2:
        if match1: layer = yp.layers[int(match1.group(1))]
        else: layer = yp.layers[int(match2.group(1))]

        rearrange_layer_nodes(layer)
        reconnect_layer_nodes(layer)

    elif match3:
        channel = yp.channels[int(match3.group(1))]
        rearrange_yp_nodes(self.id_data)
        reconnect_yp_nodes(self.id_data)

    #return

    #nodes = tree.nodes
    #
    #if self.type == 'RGB_TO_INTENSITY':
    #    rgb2i = nodes.get(self.rgb2i)

    #    if yp.disable_quick_toggle:
    #        rgb2i.mute = not self.enable
    #    else: 
    #        rgb2i.mute = False

    #    rgb2i.inputs['Intensity'].default_value = 1.0 if self.enable else 0.0

    #elif self.type == 'INTENSITY_TO_RGB':
    #    i2rgb = nodes.get(self.i2rgb)

    #    if yp.disable_quick_toggle:
    #        i2rgb.mute = not self.enable
    #    else: i2rgb.mute = False

    #    i2rgb.inputs['Intensity'].default_value = 1.0 if self.enable else 0.0

    #elif self.type == 'OVERRIDE_COLOR':
    #    oc = nodes.get(self.oc)

    #    if yp.disable_quick_toggle:
    #        oc.mute = not self.enable
    #    else: oc.mute = False

    #    oc.inputs['Intensity'].default_value = 1.0 if self.enable else 0.0

    #elif self.type == 'INVERT':
    #    invert = nodes.get(self.invert)

    #    if yp.disable_quick_toggle:
    #        invert.mute = not self.enable
    #    else: invert.mute = False

    #    update_invert_channel(self, context)

    #elif self.type == 'COLOR_RAMP':

    #    color_ramp_mix_rgb = nodes.get(self.color_ramp_mix_rgb)
    #    color_ramp_mix_rgb.inputs['Fac'].default_value = 1.0 if self.enable else 0.0

    #    color_ramp_mix_alpha = nodes.get(self.color_ramp_mix_alpha)
    #    color_ramp_mix_alpha.inputs['Fac'].default_value = 1.0 if self.enable else 0.0

    #    if yp.disable_quick_toggle:
    #        color_ramp_mix_rgb.mute = not self.enable
    #        color_ramp_mix_alpha.mute = not self.enable
    #    else:
    #        color_ramp_mix_rgb.mute = False
    #        color_ramp_mix_alpha.mute = False

    #elif self.type == 'RGB_CURVE':
    #    rgb_curve = nodes.get(self.rgb_curve)
    #    rgb_curve.inputs['Fac'].default_value = 1.0 if self.enable else 0.0

    #    if yp.disable_quick_toggle:
    #        rgb_curve.mute = not self.enable
    #    else: rgb_curve.mute = False

    #elif self.type == 'HUE_SATURATION':
    #    huesat = nodes.get(self.huesat)
    #    huesat.inputs['Fac'].default_value = 1.0 if self.enable else 0.0

    #    if yp.disable_quick_toggle:
    #        huesat.mute = not self.enable
    #    else: huesat.mute = False

    #elif self.type == 'BRIGHT_CONTRAST':
    #    brightcon = nodes.get(self.brightcon)

    #    if yp.disable_quick_toggle:
    #        brightcon.mute = not self.enable
    #    else: brightcon.mute = False

    #    update_brightcon_value(self, context)

    #elif self.type == 'MULTIPLIER':
    #    multiplier = nodes.get(self.multiplier)

    #    if yp.disable_quick_toggle:
    #        multiplier.mute = not self.enable
    #    else: multiplier.mute = False

    #    update_use_clamp(self, context)
    #    update_multiplier_val_input(self, context)

def update_modifier_shortcut(self, context):

    yp = self.id_data.yp
    if yp.halt_update: return

    mod = self

    if mod.shortcut:

        match1 = re.match(r'yp\.layers\[(\d+)\]\.channels\[(\d+)\]\.modifiers\[(\d+)\]', mod.path_from_id())
        match2 = re.match(r'yp\.layers\[(\d+)\]\.modifiers\[(\d+)\]', mod.path_from_id())
        match3 = re.match(r'yp\.channels\[(\d+)\]\.modifiers\[(\d+)\]', mod.path_from_id())

        if match1 or match2:

            layer = yp.layers[int(match1.group(1))]
            layer.color_shortcut = False

            for m in layer.modifiers:
                if m != mod:
                    m.shortcut = False

            for ch in layer.channels:
                for m in ch.modifiers:
                    if m != mod:
                        m.shortcut = False

        elif match3:
            channel = yp.channels[int(match2.group(1))]
            for m in channel.modifiers:
                if m != mod: 
                    m.shortcut = False

def update_invert_channel(self, context):
    yp = self.id_data.yp
    if yp.halt_update or not self.enable: return
    channel_type = get_modifier_channel_type(self)
    tree = get_mod_tree(self)
    invert = tree.nodes.get(self.invert)

    invert.inputs[2].default_value = 1.0 if self.invert_r_enable and self.enable else 0.0
    if channel_type == 'VALUE':
        invert.inputs[3].default_value = 1.0 if self.invert_a_enable and self.enable else 0.0
    else:
        invert.inputs[3].default_value = 1.0 if self.invert_g_enable and self.enable else 0.0
        invert.inputs[4].default_value = 1.0 if self.invert_b_enable and self.enable else 0.0
        invert.inputs[5].default_value = 1.0 if self.invert_a_enable and self.enable else 0.0

def update_use_clamp(self, context):
    yp = self.id_data.yp
    if yp.halt_update or not self.enable: return
    tree = get_mod_tree(self)
    channel_type = get_modifier_channel_type(self)

    if self.type == 'MULTIPLIER':
        multiplier = tree.nodes.get(self.multiplier)
        multiplier.inputs[2].default_value = 1.0 if self.use_clamp and self.enable else 0.0
    elif self.type == 'MATH':
        math = tree.nodes.get(self.math)
        math.node_tree.nodes.get('Math.R').use_clamp = self.use_clamp
        math.node_tree.nodes.get('Math.A').use_clamp = self.use_clamp
        if channel_type != 'VALUE':
            math.node_tree.nodes.get('Math.G').use_clamp = self.use_clamp
            math.node_tree.nodes.get('Math.B').use_clamp = self.use_clamp

def update_affect_alpha(self, context):
    yp = self.id_data.yp
    if yp.halt_update or not self.enable: return
    tree = get_mod_tree(self)

    if self.type == 'MATH':
        math = tree.nodes.get(self.math).node_tree
        alpha = math.nodes.get('Mix.A')
        if self.affect_alpha:
            alpha.mute = False
        else:
            alpha.mute = True

def update_math_method(self, context):
    yp = self.id_data.yp
    if yp.halt_update or not self.enable: return
    tree = get_mod_tree(self)

    if self.type == 'MATH':
        math = tree.nodes.get(self.math)
        math.node_tree.nodes.get('Math.R').operation = self.math_meth
        math.node_tree.nodes.get('Math.G').operation = self.math_meth
        math.node_tree.nodes.get('Math.B').operation = self.math_meth
        math.node_tree.nodes.get('Math.A').operation = self.math_meth

def update_multiplier_val_input(self, context):

    yp = self.id_data.yp
    if yp.halt_update or not self.enable: return
    channel_type = get_modifier_channel_type(self)
    tree = get_mod_tree(self)

    if self.type == 'MULTIPLIER':
        multiplier = tree.nodes.get(self.multiplier)
        multiplier.inputs[3].default_value = self.multiplier_r_val if self.enable else 1.0
        if channel_type == 'VALUE':
            multiplier.inputs[4].default_value = self.multiplier_a_val if self.enable else 1.0
        else:
            multiplier.inputs[4].default_value = self.multiplier_g_val if self.enable else 1.0
            multiplier.inputs[5].default_value = self.multiplier_b_val if self.enable else 1.0
            multiplier.inputs[6].default_value = self.multiplier_a_val if self.enable else 1.0

def update_math_val_input(self, context):
    yp = self.id_data.yp
    if yp.halt_update or not self.enable: return
    channel_type = get_modifier_channel_type(self)
    tree = get_mod_tree(self)

    if self.type == 'MATH':
        math = tree.nodes.get(self.math)
        math.inputs[2].default_value = self.math_r_val if self.enable else 0.0
        if channel_type == 'VALUE':
            math.inputs[3].default_value = self.math_a_val if self.enable else 0.0
        else:
            math.inputs[3].default_value = self.math_g_val if self.enable else 0.0
            math.inputs[4].default_value = self.math_b_val if self.enable else 0.0
            math.inputs[5].default_value = self.math_a_val if self.enable else 0.0

def update_brightcon_value(self, context):

    yp = self.id_data.yp
    if yp.halt_update or not self.enable: return
    channel_type = get_modifier_channel_type(self)
    tree = get_mod_tree(self)

    if self.type == 'BRIGHT_CONTRAST':
        brightcon = tree.nodes.get(self.brightcon)
        brightcon.inputs['Bright'].default_value = self.brightness_value if self.enable else 0.0
        brightcon.inputs['Contrast'].default_value = self.contrast_value if self.enable else 0.0

def update_huesat_value(self, context):

    yp = self.id_data.yp
    if yp.halt_update or not self.enable: return
    channel_type = get_modifier_channel_type(self)
    tree = get_mod_tree(self)

    if self.type == 'HUE_SATURATION':
        huesat = tree.nodes.get(self.huesat)
        huesat.inputs['Hue'].default_value = self.huesat_hue_val if self.enable else 0.0
        huesat.inputs['Saturation'].default_value = self.huesat_saturation_val if self.enable else 0.0
        huesat.inputs['Value'].default_value = self.huesat_value_val if self.enable else 0.0

def update_rgb2i_col(self, context):
    yp = self.id_data.yp
    if yp.halt_update or not self.enable: return
    tree = get_mod_tree(self)

    if self.type == 'RGB_TO_INTENSITY':
        rgb2i = tree.nodes.get(self.rgb2i)
        rgb2i.inputs['RGB To Intensity Color'].default_value = self.rgb2i_col

def update_oc_col(self, context):

    yp = self.id_data.yp
    if yp.halt_update or not self.enable: return
    channel_type = get_modifier_channel_type(self)
    tree = get_mod_tree(self)

    if self.type == 'OVERRIDE_COLOR': #and not self.oc_use_normal_base:
        oc = tree.nodes.get(self.oc)

        if channel_type == 'VALUE':
            col = (self.oc_val, self.oc_val, self.oc_val, 1.0)
        else: col = self.oc_col

        if oc: oc.inputs['Override Color'].default_value = col

class YPaintModifier(bpy.types.PropertyGroup):
    enable : BoolProperty(default=True, update=update_modifier_enable)
    name : StringProperty(default='')

    type : EnumProperty(
        name = 'Modifier Type',
        items = modifier_type_items,
        default = 'INVERT')

    # RGB to Intensity nodes
    rgb2i : StringProperty(default='')

    rgb2i_col : FloatVectorProperty(name='RGB to Intensity Color', size=4, subtype='COLOR', 
            default=(1.0,0.0,1.0,1.0), min=0.0, max=1.0,
            update=update_rgb2i_col)

    # Intensity to RGB nodes
    i2rgb : StringProperty(default='')

    # Override Color nodes (Deprecated)
    oc : StringProperty(default='')

    oc_col : FloatVectorProperty(name='Override Color', size=4, subtype='COLOR', 
            default=(1.0,1.0,1.0,1.0), min=0.0, max=1.0,
            update=update_oc_col)

    oc_val : FloatProperty(name='Override Value', subtype='FACTOR', 
            default=1.0, min=0.0, max=1.0,
            update=update_oc_col)

    # Invert nodes
    invert : StringProperty(default='')

    # Invert toggles
    invert_r_enable : BoolProperty(default=True, update=update_invert_channel)
    invert_g_enable : BoolProperty(default=True, update=update_invert_channel)
    invert_b_enable : BoolProperty(default=True, update=update_invert_channel)
    invert_a_enable : BoolProperty(default=False, update=update_invert_channel)

    # Color Ramp nodes
    color_ramp : StringProperty(default='')
    color_ramp_linear_start : StringProperty(default='')
    color_ramp_linear : StringProperty(default='')
    color_ramp_alpha_multiply : StringProperty(default='')
    color_ramp_mix_rgb : StringProperty(default='')
    color_ramp_mix_alpha : StringProperty(default='')

    # RGB Curve nodes
    rgb_curve : StringProperty(default='')

    # Brightness Contrast nodes
    brightcon : StringProperty(default='')

    brightness_value : FloatProperty(name='Brightness', description='Brightness', 
            default=0.0, min=-100.0, max=100.0, update=update_brightcon_value)
    contrast_value : FloatProperty(name='Contrast', description='Contrast', 
            default=0.0, min=-100.0, max=100.0, update=update_brightcon_value)

    # Hue Saturation nodes
    huesat : StringProperty(default='')

    huesat_hue_val : FloatProperty(default=0.5, min=0.0, max=1.0, description='Hue', update=update_huesat_value)
    huesat_saturation_val : FloatProperty(default=1.0, min=0.0, max=2.0, description='Saturation', update=update_huesat_value)
    huesat_value_val : FloatProperty(default=1.0, min=0.0, max=2.0, description='Value', update=update_huesat_value)

    # Multiplier nodes (Deprecated)
    multiplier : StringProperty(default='')

    multiplier_r_val : FloatProperty(default=1.0, update=update_multiplier_val_input)
    multiplier_g_val : FloatProperty(default=1.0, update=update_multiplier_val_input)
    multiplier_b_val : FloatProperty(default=1.0, update=update_multiplier_val_input)
    multiplier_a_val : FloatProperty(default=1.0, update=update_multiplier_val_input)

    # Math nodes
    math : StringProperty(default='')

    math_r_val : FloatProperty(default=1.0, update=update_math_val_input)
    math_g_val : FloatProperty(default=1.0, update=update_math_val_input)
    math_b_val : FloatProperty(default=1.0, update=update_math_val_input)
    math_a_val : FloatProperty(default=1.0, update=update_math_val_input)

    math_meth : EnumProperty(
        name = 'Method',
        items = math_method_items,
        default = "MULTIPLY",
        update = update_math_method)

    affect_alpha : BoolProperty(name='Affect Alpha', default=False, update=update_affect_alpha) 

    # Individual modifier node frame
    frame : StringProperty(default='')

    # Clamp prop is available in some modifiers
    use_clamp : BoolProperty(name='Use Clamp', default=False, update=update_use_clamp)

    shortcut : BoolProperty(
            name = 'Property Shortcut',
            description = 'Property shortcut on layer list (currently only available on RGB to Intensity)',
            default=False,
            update=update_modifier_shortcut)

    expand_content : BoolProperty(default=True)

def enable_modifiers_tree(parent, rearrange = False):
    
    group_tree = parent.id_data
    yp = group_tree.yp

    match1 = re.match(r'^yp\.layers\[(\d+)\]\.channels\[(\d+)\]$', parent.path_from_id())
    match2 = re.match(r'^yp\.layers\[(\d+)\]$', parent.path_from_id())
    if match1:
        layer = yp.layers[int(match1.group(1))]
        root_ch = yp.channels[int(match1.group(2))]
        ch = parent
        name = root_ch.name + ' ' + layer.name
        if (layer.type in {'BACKGROUND', 'COLOR', 'OBJECT_INDEX'} and not ch.override) or (ch.override and ch.override_type in {'DEFAULT'}):
            return
    elif match2:
        layer = parent
        name = layer.name
        if layer.type in {'IMAGE', 'VCOL', 'BACKGROUND', 'COLOR', 'GROUP', 'HEMI', 'MUSGRAVE'}:
            return
    else:
        return

    if len(parent.modifiers) == 0:
        return None

    # Check if modifier tree already available
    if parent.mod_group != '': 
        return 

    # Create modifier tree
    mod_tree = bpy.data.node_groups.new('~yP Modifiers ' + name, 'ShaderNodeTree')

    mod_tree.inputs.new('NodeSocketColor', 'RGB')
    mod_tree.inputs.new('NodeSocketFloat', 'Alpha')
    mod_tree.outputs.new('NodeSocketColor', 'RGB')
    mod_tree.outputs.new('NodeSocketFloat', 'Alpha')

    # New inputs and outputs
    mod_tree_start = mod_tree.nodes.new('NodeGroupInput')
    mod_tree_start.name = MOD_TREE_START
    mod_tree_end = mod_tree.nodes.new('NodeGroupOutput')
    mod_tree_end.name = MOD_TREE_END

    if match2 and layer.source_group != '':
        layer_tree = get_source_tree(layer)
    else: layer_tree = get_tree(layer)

    # Create main modifier group
    mod_group = new_node(layer_tree, parent, 'mod_group', 'ShaderNodeGroup', 'mod_group')
    mod_group.node_tree = mod_tree

    if match1:
        # Create modifier group neighbor
        mod_n = new_node(layer_tree, parent, 'mod_n', 'ShaderNodeGroup', 'mod_n')
        mod_s = new_node(layer_tree, parent, 'mod_s', 'ShaderNodeGroup', 'mod_s')
        mod_e = new_node(layer_tree, parent, 'mod_e', 'ShaderNodeGroup', 'mod_e')
        mod_w = new_node(layer_tree, parent, 'mod_w', 'ShaderNodeGroup', 'mod_w')
        mod_n.node_tree = mod_tree
        mod_s.node_tree = mod_tree
        mod_e.node_tree = mod_tree
        mod_w.node_tree = mod_tree
    elif match2:
        mod_group_1 = new_node(layer_tree, parent, 'mod_group_1', 'ShaderNodeGroup', 'mod_group_1')
        mod_group_1.node_tree = mod_tree

    for mod in parent.modifiers:
        check_modifier_nodes(mod, mod_tree, layer_tree)

    if rearrange:
        rearrange_layer_nodes(layer)
        reconnect_layer_nodes(layer)

    return mod_tree

def disable_modifiers_tree(parent, rearrange=False):
    group_tree = parent.id_data
    yp = group_tree.yp

    match1 = re.match(r'^yp\.layers\[(\d+)\]\.channels\[(\d+)\]$', parent.path_from_id())
    match2 = re.match(r'^yp\.layers\[(\d+)\]$', parent.path_from_id())
    if match1: 
        layer = yp.layers[int(match1.group(1))]
        root_ch = yp.channels[int(match1.group(2))]

        # Check if fine bump map is still used
        if parent.enable and len(parent.modifiers) > 0 and root_ch.type == 'NORMAL' and root_ch.enable_smooth_bump:
            if layer.type not in {'BACKGROUND', 'COLOR', 'OBJECT_INDEX'} and not parent.override:
                return
            if parent.override and parent.override_type != 'DEFAULT':
                return

        #if (len(parent.modifiers) > 0 and root_ch.type == 'NORMAL' and root_ch.enable_smooth_bump and parent.override) or (parent.override and parent.override_type != 'DEFAULT'):
            #parent.normal_map_type == 'FINE_BUMP_MAP'
            #or (parent.enable_transition_bump and parent.transition_bump_type in {'FINE_BUMP_MAP', 'CURVED_BUMP_MAP'})
            #return

    elif match2:
        layer = parent
        if layer.type in {'IMAGE', 'VCOL', 'BACKGROUND', 'COLOR', 'GROUP', 'MUSGRAVE'}:
            return
    else:
        return

    # Check if modifier tree already gone
    if parent.mod_group == '': return

    if match2 and layer.source_group != '':
        layer_tree = get_source_tree(layer)
    else: layer_tree = get_tree(layer)

    # Get modifier group
    mod_group = layer_tree.nodes.get(parent.mod_group)

    # Add new copied modifier nodes on layer tree
    for mod in parent.modifiers:
        check_modifier_nodes(mod, layer_tree, mod_group.node_tree)

    # Remove modifier tree
    remove_node(layer_tree, parent, 'mod_group')

    if match1:
        # Remove modifier group neighbor
        remove_node(layer_tree, parent, 'mod_n')
        remove_node(layer_tree, parent, 'mod_s')
        remove_node(layer_tree, parent, 'mod_e')
        remove_node(layer_tree, parent, 'mod_w')
    elif match2:
        remove_node(layer_tree, parent, 'mod_group_1')

    if rearrange:
        rearrange_layer_nodes(layer)
        reconnect_layer_nodes(layer)

def register():
    bpy.utils.register_class(YNewYPaintModifier)
    bpy.utils.register_class(YMoveYPaintModifier)
    bpy.utils.register_class(YRemoveYPaintModifier)
    bpy.utils.register_class(YPaintModifier)

def unregister():
    bpy.utils.unregister_class(YNewYPaintModifier)
    bpy.utils.unregister_class(YMoveYPaintModifier)
    bpy.utils.unregister_class(YRemoveYPaintModifier)
    bpy.utils.unregister_class(YPaintModifier)
