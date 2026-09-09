"""Create a separate self-contained walkthrough file without changing the still."""
import bpy, importlib.util, json
from pathlib import Path
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT.parent / 'ForestPath_Local_Packed.blend'
OUTPUT = ROOT.parent / 'ForestPath_Walk_Packed.blend'
if not SOURCE.exists():
    SOURCE = ROOT / 'scenes/ForestPath.blend'
bpy.ops.wm.open_mainfile(filepath=str(SOURCE), use_scripts=False)
original_camera = [list(row) for row in bpy.context.scene.camera.matrix_world]
spec = importlib.util.spec_from_file_location('forest_walk', ROOT/'tools/walk_mode.py')
walk = importlib.util.module_from_spec(spec)
spec.loader.exec_module(walk)
walk.configure()
walk.register()
for image in bpy.data.images:
    if image.users and image.source == 'FILE' and not image.packed_file:
        if not Path(bpy.path.abspath(image.filepath)).is_file():
            raise RuntimeError('Missing texture: '+image.filepath)
        image.pack()
bpy.context.scene['distribution'] = 'Local user copy with licensed Megascans images. Do not redistribute publicly.'
bpy.context.scene['walk_help'] = 'Start_Walk.cmd configures gravity and adds the walk button. Direct opening: F3 > Walk Navigation; Tab toggles gravity.'
bpy.context.scene.render.filepath = str(ROOT/'renders/walk_view.png')
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), compress=True)
bpy.ops.wm.open_mainfile(filepath=str(OUTPUT), use_scripts=False)
scene = bpy.context.scene
assert scene.render.engine == 'BLENDER_EEVEE'
assert original_camera == [list(row) for row in scene.camera.matrix_world], 'Still camera was changed'
reopened_shading = [a.spaces.active.shading.type for a in bpy.context.screen.areas if a.type == 'VIEW_3D']
# Blender may downgrade a saved rendered viewport on load. The launcher restores it.
walk.configure()
images = [im for im in bpy.data.images if im.users and im.source == 'FILE']
assert all(im.packed_file for im in images)
eye, rotation = walk.start_pose(scene)
checked = []
for area in bpy.context.screen.areas:
    if area.type != 'VIEW_3D':
        continue
    rv = area.spaces.active.region_3d
    actual = rv.view_location - rv.view_rotation @ Vector((0, 0, -rv.view_distance))
    assert (actual-eye).length < .001
    assert rv.view_perspective == 'PERSP'
    assert area.spaces.active.shading.type == 'RENDERED'
    region = next(r for r in area.regions if r.type == 'WINDOW')
    with bpy.context.temp_override(area=area, region=region):
        assert bpy.ops.view3d.walk.poll()
    checked.append(area.type)
assert checked
report = {'blender': bpy.app.version_string, 'file': OUTPUT.name, 'engine': scene.render.engine,
          'packed_images': len(images), 'camera_unchanged': True, 'start_eye_m': list(eye),
          'eye_height_m': walk.EYE_HEIGHT, 'walk_speed_m_s': walk.WALK_SPEED,
          'gravity': bpy.context.preferences.inputs.walk_navigation.use_gravity,
          'viewports_checked': len(checked), 'native_walk_operator_available': True,
          'reopened_shading': reopened_shading, 'launcher_shading': 'RENDERED',
          'interactive_input_tested': False}
(ROOT/'docs/walk_validation.json').write_text(json.dumps(report, indent=2))
print('WALK_FILE_VALIDATED', json.dumps(report), flush=True)
