"""Blender viewport walking profile. Run through Start_Walk.cmd or Text Editor.

Uses Blender's native navigation operator; does not install an addon or save
global preferences. The original render camera is never moved.
"""
import bpy
from mathutils import Vector

EYE_HEIGHT = 1.65
WALK_SPEED = 1.8


def start_pose(scene):
    camera = scene.camera
    eye = camera.matrix_world.translation.copy()
    terrain = next(o for o in scene.objects if o.name == 'Eroded trail and asymmetric banks')
    evaluated = terrain.evaluated_get(bpy.context.evaluated_depsgraph_get())
    inverse = evaluated.matrix_world.inverted()
    origin = inverse @ Vector((eye.x, eye.y, 20))
    direction = (inverse.to_3x3() @ Vector((0, 0, -1))).normalized()
    hit, location, _, _ = evaluated.ray_cast(origin, direction)
    if not hit:
        raise RuntimeError('The walking start must be above the trail terrain')
    floor = evaluated.matrix_world @ location
    eye.z = floor.z + EYE_HEIGHT
    return eye, camera.matrix_world.to_quaternion()


def set_view(area, scene):
    eye, rotation = start_pose(scene)
    space = area.spaces.active
    view = space.region_3d
    view.view_rotation = rotation
    view.view_distance = 8.0
    view.view_location = eye + rotation @ Vector((0, 0, -8.0))
    view.view_perspective = 'PERSP'
    space.lens = scene.camera.data.lens
    space.clip_start = .05
    space.clip_end = 300
    space.lock_camera = False
    space.overlay.show_overlays = False
    space.show_gizmo = False
    space.shading.type = 'RENDERED'
    space.shading.use_scene_lights_render = True
    space.shading.use_scene_world_render = True
    space.shading.use_scene_lights = True
    space.shading.use_scene_world = True
    area.tag_redraw()


def configure():
    scene = bpy.context.scene
    if scene.camera is None:
        raise RuntimeError('Open the forest scene before enabling walking')
    preferences = bpy.context.preferences
    preferences.use_preferences_save = False
    preferences.inputs.navigation_mode = 'WALK'
    walk = preferences.inputs.walk_navigation
    walk.use_gravity = True
    walk.view_height = EYE_HEIGHT
    walk.walk_speed = WALK_SPEED
    walk.walk_speed_factor = 2.5
    walk.mouse_speed = .8
    walk.jump_height = .3
    scene.render.engine = 'BLENDER_EEVEE'
    scene.eevee.taa_samples = 16
    scene.eevee.taa_render_samples = 64
    scene.eevee.use_raytracing = False
    scene.eevee.use_shadow_jitter_viewport = False
    scene.render.use_simplify = True
    scene.render.simplify_subdivision = 0
    # A giant volume box is unsuitable as a navigation surface and costs frames.
    for obj in scene.objects:
        if obj.name.startswith('Aerial perspective'):
            obj.hide_viewport = True
    scene['walk_profile'] = 'WASD + mouse; native Blender walk; eye 1.65m; speed 1.8m/s'
    scene['walk_render_note'] = 'EEVEE navigation view. Original Cycles scene is a separate file.'
    configured = 0
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type == 'VIEW_3D':
                set_view(area, scene)
                configured += 1
    if not configured:
        raise RuntimeError('No 3D viewport is available')
    return configured


class FOREST_OT_start_walk(bpy.types.Operator):
    bl_idname = 'forest.start_walk'
    bl_label = '森を歩く'
    bl_description = 'WASDとマウスで移動。左クリックで終了、Escで開始地点へ戻る'

    @classmethod
    def poll(cls, context):
        return context.area is not None and context.area.type == 'VIEW_3D'

    def execute(self, context):
        if context.space_data.region_3d.view_perspective == 'CAMERA':
            set_view(context.area, context.scene)
        region = next(r for r in context.area.regions if r.type == 'WINDOW')
        with context.temp_override(region=region):
            bpy.ops.view3d.walk('INVOKE_DEFAULT')
        return {'FINISHED'}


class FOREST_OT_reset_view(bpy.types.Operator):
    bl_idname = 'forest.reset_view'
    bl_label = '小道の入口へ'
    bl_description = '撮影用カメラを動かさず、歩行視点を入口へ戻す'

    @classmethod
    def poll(cls, context):
        return context.area is not None and context.area.type == 'VIEW_3D'

    def execute(self, context):
        set_view(context.area, context.scene)
        return {'FINISHED'}


def draw_controls(self, context):
    if not context.scene.get('walk_profile'):
        return
    row = self.layout.row(align=True)
    row.separator()
    row.operator('forest.start_walk', text='森を歩く', icon='PLAY')
    row.operator('forest.reset_view', text='', icon='HOME')


def register():
    # Safe to rerun from the Text Editor in the same process.
    for cls in (FOREST_OT_start_walk, FOREST_OT_reset_view):
        old = getattr(bpy.types, cls.__name__, None)
        if old:
            bpy.utils.unregister_class(old)
        bpy.utils.register_class(cls)
    previous = bpy.app.driver_namespace.get('forest_walk_header')
    if previous:
        bpy.types.VIEW3D_HT_header.remove(previous)
    bpy.types.VIEW3D_HT_header.append(draw_controls)
    bpy.app.driver_namespace['forest_walk_header'] = draw_controls


if __name__ == '__main__':
    configure()
    register()
    print('FOREST_WALK_READY: click 森を歩く in the viewport header, or use F3 > Walk Navigation', flush=True)
