"""Render the saved scene, validate dependencies, and record measured settings."""
import bpy, json, time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'scenes/ForestPath.blend'),load_ui=False,use_scripts=False)
s=bpy.context.scene
missing=[]
for im in bpy.data.images:
    if im.source=='FILE' and im.users and not im.packed_file and not Path(bpy.path.abspath(im.filepath)).is_file():missing.append(im.filepath)
if missing:raise RuntimeError('Missing images: '+str(missing))
pref=bpy.context.preferences.addons['cycles'].preferences;pref.compute_device_type='OPTIX';pref.get_devices()
for d in pref.devices:d.use=d.type=='OPTIX'
s.cycles.device='GPU';s.cycles.samples=512;s.cycles.adaptive_threshold=.007;s.cycles.adaptive_min_samples=64
s.render.resolution_x=3840;s.render.resolution_y=2560;s.render.resolution_percentage=100
s.render.image_settings.file_format='PNG';s.render.image_settings.color_mode='RGB';s.render.image_settings.color_depth='16';s.render.filepath=str(ROOT/'renders/forest_path.png')
s.unit_settings.system='METRIC'
# Eliminate unused imported datablocks without touching scene members.
bpy.data.orphans_purge(do_recursive=True)
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'scenes/ForestPath.blend'),compress=True)
t=time.time();bpy.ops.render.render(write_still=True);elapsed=time.time()-t
s.render.image_settings.file_format='JPEG';s.render.image_settings.quality=95
bpy.data.images['Render Result'].save_render(str(ROOT/'renders/forest_path.jpg'),scene=s)
s.render.image_settings.file_format='OPEN_EXR';s.render.image_settings.color_depth='16';s.render.image_settings.exr_codec='ZIP'
bpy.data.images['Render Result'].save_render(str(ROOT/'renders/forest_path_linear.exr'),scene=s)
s.render.image_settings.file_format='PNG';s.render.image_settings.color_depth='16'
report={'blender':bpy.app.version_string,'engine':s.render.engine,'device':[(d.name,d.type) for d in pref.devices if d.use],'render_seconds':round(elapsed,2),'resolution':[s.render.resolution_x,s.render.resolution_y],'maximum_samples':s.cycles.samples,'adaptive_noise_threshold':s.cycles.adaptive_threshold,'minimum_samples':s.cycles.adaptive_min_samples,'denoiser':s.cycles.denoiser,'view_transform':s.view_settings.view_transform,'look':s.view_settings.look,'exposure':s.view_settings.exposure,'camera_mm':s.camera.data.lens,'f_stop':s.camera.data.dof.aperture_fstop,'focus_distance_m':s.camera.data.dof.focus_distance,'objects':len(s.objects),'mesh_objects':sum(o.type=='MESH' for o in s.objects),'unique_meshes':len(bpy.data.meshes),'missing_images':missing,'megascans_materials':[m.name for m in bpy.data.materials if 'Megascans' in m.name],'collections':{c.name:len(c.objects) for c in s.collection.children},'imagegen_used':False}
(ROOT/'docs/validation.json').write_text(json.dumps(report,indent=2))
print('FINAL_RENDER_VALIDATED',json.dumps(report),flush=True)
