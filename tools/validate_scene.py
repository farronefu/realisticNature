"""Reopen both deliveries and check portable dependencies and moss coverage."""
import bpy, json, hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
report={}
for key,path in [('repository',ROOT/'scenes/ForestPath.blend'),('local_packed',ROOT.parent/'ForestPath_Local_Packed.blend')]:
    bpy.ops.wm.open_mainfile(filepath=str(path),load_ui=False,use_scripts=False)
    images=[im for im in bpy.data.images if im.users and im.source=='FILE']
    packed=[im.name for im in images if im.packed_file]
    missing=[im.name for im in images if not im.packed_file and not Path(bpy.path.abspath(im.filepath)).is_file()]
    assert not missing,missing
    assert len(packed)==(len(images) if key=='local_packed' else 0),(key,packed)
    moss_rock_materials=[]
    for mat in bpy.data.materials:
        if not mat.use_nodes:continue
        nodes=mat.node_tree.nodes
        masks=[n for n in nodes if n.type=='TEX_IMAGE' and n.image and '_Opacity.jpg' in n.image.name and n.projection=='BOX']
        for mask in masks:
            assert mask.image.colorspace_settings.name=='Non-Color'
            assert any(link.to_node.type=='MATH' and link.to_node.operation=='MULTIPLY' for link in mask.outputs['Color'].links)
            moss_rock_materials.append(mat.name)
    assert moss_rock_materials,'No rock material has a connected scanned opacity mask'
    covered_meshes={ob.data.name for ob in bpy.context.scene.objects if ob.type=='MESH' and any(mat and mat.name in moss_rock_materials for mat in ob.data.materials)}
    assert len(covered_meshes)>=6,covered_meshes
    report[key]={'file':path.name,'bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'objects':len(bpy.context.scene.objects),'used_images':len(images),'packed_images':len(packed),'missing_images':missing,'rock_moss_opacity_materials':moss_rock_materials}
(ROOT/'docs/local_package_validation.json').write_text(json.dumps(report,indent=2))
print('REOPEN_VALIDATION_OK',json.dumps(report),flush=True)
