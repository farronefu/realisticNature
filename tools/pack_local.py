"""Make a self-contained local copy; never upload this licensed-asset bundle to Git."""
import bpy,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
out=ROOT.parent/'ForestPath_Local_Packed.blend'
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'scenes/ForestPath.blend'),load_ui=False,use_scripts=False)
for im in bpy.data.images:
    if im.source=='FILE' and im.users and not im.packed_file:
        path=Path(bpy.path.abspath(im.filepath))
        if not path.is_file():raise RuntimeError('Missing '+str(path))
        im.pack()
bpy.context.scene['distribution']='Local user copy with licensed Megascans images embedded. Do not redistribute this file publicly.'
bpy.ops.wm.save_as_mainfile(filepath=str(out),compress=True)
unpacked=[im.name for im in bpy.data.images if im.users and im.source=='FILE' and not im.packed_file]
if unpacked:raise RuntimeError('Not packed: '+str(unpacked))
print('PACKED_COPY_OK',out,flush=True)
