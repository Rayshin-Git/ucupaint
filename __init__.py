bl_info = {
    "name": "Ucupaint",
    "author": "Yusuf Umar, Agni Rakai Sahakarya, Jan Bláha",
    "version": (1, 0, 12),
    "blender": (2, 80, 0),
    "location": "Node Editor > Properties > Ucupaint",
    "description": "Special node to manage painting layers for Cycles and Eevee materials",
    "wiki_url": "https://ucupumar.github.io/ucupaint-wiki/",
    "category": "Node",
}

if "bpy" in locals():
    import imp
    imp.reload(image_ops)
    imp.reload(common)
    imp.reload(bake_common)
    imp.reload(lib)
    imp.reload(ui)
    imp.reload(subtree)
    imp.reload(transition_common)
    imp.reload(input_outputs)
    imp.reload(node_arrangements)
    imp.reload(node_connections)
    imp.reload(preferences)
    imp.reload(vcol_editor)
    imp.reload(transition)
    imp.reload(BakeInfo)
    imp.reload(ImageAtlas)
    imp.reload(MaskModifier)
    imp.reload(Mask)
    imp.reload(Modifier)
    imp.reload(NormalMapModifier)
    imp.reload(Layer)
    imp.reload(Bake)
    imp.reload(BakeToLayer)
    imp.reload(Root)
    imp.reload(load_blend_updates)
else:
    from . import image_ops, common, bake_common, lib, ui, subtree, transition_common, input_outputs, node_arrangements, node_connections, preferences
    from . import vcol_editor, transition, BakeInfo, ImageAtlas, MaskModifier, Mask, Modifier, NormalMapModifier, Layer, Bake, BakeToLayer, Root, load_blend_updates

import bpy 

def register():
    image_ops.register()
    preferences.register()
    lib.register()
    ui.register()
    vcol_editor.register()
    transition.register()
    BakeInfo.register()
    ImageAtlas.register()
    MaskModifier.register()
    Mask.register()
    Modifier.register()
    NormalMapModifier.register()
    Layer.register()
    Bake.register()
    BakeToLayer.register()
    Root.register()
    load_blend_updates.register()

    print('INFO: ' + bl_info['name'] + ' ' + common.get_current_version_str() + ' is registered!')

def unregister():
    image_ops.unregister()
    preferences.unregister()
    lib.unregister()
    ui.unregister()
    vcol_editor.unregister()
    transition.unregister()
    BakeInfo.unregister()
    ImageAtlas.unregister()
    MaskModifier.unregister()
    Mask.unregister()
    Modifier.unregister()
    NormalMapModifier.unregister()
    Layer.unregister()
    Bake.unregister()
    BakeToLayer.unregister()
    Root.unregister()
    load_blend_updates.unregister()

    print('INFO: ' + bl_info['name'] + ' ' + common.get_current_version_str() + ' is unregistered!')

if __name__ == "__main__":
    register()
