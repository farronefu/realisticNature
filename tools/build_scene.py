"""Build a camera-composed, physically scaled forest path in Blender/Cycles."""
import bpy, math, random, json, sys, argparse
from pathlib import Path
from mathutils import Vector, Matrix, noise
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[1]; A=ROOT/'assets'
parser=argparse.ArgumentParser();parser.add_argument('--preview',action='store_true');args=parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
r=random.Random(70923)
bpy.ops.wm.read_factory_settings(use_empty=True)
scene=bpy.context.scene
COL={}
for name in ['01 Terrain','02 Hero rocks','03 Forest trees','04 Ferns and understory','05 Roots and deadwood','06 Leaf litter','07 Canopy','08 Lighting','09 Camera']:
    c=bpy.data.collections.new(name);scene.collection.children.link(c);COL[name]=c
def link(o,group): COL[group].objects.link(o);return o
def mesh(name,v,f,mat,group,uv=None):
    me=bpy.data.meshes.new(name);me.from_pydata(v,[],f);me.update()
    o=link(bpy.data.objects.new(name,me),group)
    if mat: me.materials.append(mat)
    for p in me.polygons:p.use_smooth=True
    if uv:
        layer=me.uv_layers.new(name='UVMap')
        for p in me.polygons:
            for i in p.loop_indices:layer.data[i].uv=uv[me.loops[i].vertex_index]
    return o
def image(path,data=False):
    im=bpy.data.images.load(str(path),check_existing=True)
    if data:im.colorspace_settings.name='Non-Color'
    return im
def pbr(name,folder,prefix,uvscale=1):
    m=bpy.data.materials.new(name);m.use_nodes=True;n=m.node_tree.nodes;l=m.node_tree.links;n.clear()
    out=n.new('ShaderNodeOutputMaterial');out.location=(700,0)
    p=n.new('ShaderNodeBsdfPrincipled');p.location=(400,0);l.new(p.outputs[0],out.inputs['Surface'])
    tc=n.new('ShaderNodeTexCoord');tc.location=(-800,0)
    sc=n.new('ShaderNodeVectorMath');sc.operation='SCALE';sc.inputs[3].default_value=uvscale;l.new(tc.outputs['UV'],sc.inputs[0]);sc.location=(-600,0)
    for ch,sock in [('diff','Base Color'),('rough','Roughness'),('nor_gl','Normal'),('nor_dx','Normal')]:
        files=list(folder.glob(prefix+'_'+ch+'_*'))
        if not files:continue
        t=n.new('ShaderNodeTexImage');t.image=image(files[0],ch!='diff');l.new(sc.outputs[0],t.inputs['Vector']);t.location=(-350,180-150*len(n))
        if ch.startswith('nor'):
            nm=n.new('ShaderNodeNormalMap');nm.inputs['Strength'].default_value=.7
            if ch=='nor_dx':
                inv=n.new('ShaderNodeVectorMath');inv.operation='MULTIPLY_ADD';inv.inputs[1].default_value=(1,-1,1);inv.inputs[2].default_value=(0,1,0);l.new(t.outputs['Color'],inv.inputs[0]);l.new(inv.outputs[0],nm.inputs['Color'])
            else:l.new(t.outputs['Color'],nm.inputs['Color'])
            l.new(nm.outputs[0],p.inputs['Normal'])
        else:l.new(t.outputs['Color'],p.inputs[sock])
    return m
groundmat=pbr('Forest floor | scanned 4K / 2m repeat',A/'forest_leaves_02','forest_leaves_02')
bark=pbr('Exposed roots | scanned bark',A/'bark_brown_01','bark_brown_01')
# World-space box projection prevents the top-down UV stretch on steep banks.
nt=groundmat.node_tree;geo=nt.nodes.new('ShaderNodeNewGeometry');mapping=nt.nodes.new('ShaderNodeVectorMath');mapping.operation='SCALE';mapping.inputs[3].default_value=.5;nt.links.new(geo.outputs['Position'],mapping.inputs[0])
for texnode in [n for n in nt.nodes if n.type=='TEX_IMAGE']:
    texnode.projection='BOX';texnode.projection_blend=.28;nt.links.new(mapping.outputs[0],texnode.inputs['Vector'])
p=next(n for n in nt.nodes if n.type=='BSDF_PRINCIPLED');albedo=p.inputs['Base Color'].links[0].from_socket
mul=nt.nodes.new('ShaderNodeVectorMath');mul.operation='MULTIPLY';mul.inputs[1].default_value=(.64,.71,.68);nt.links.new(albedo,mul.inputs[0]);nt.links.new(mul.outputs[0],p.inputs['Base Color'])
heighttex=nt.nodes.new('ShaderNodeTexImage');heighttex.image=image(A/'forest_leaves_02/forest_leaves_02_disp_4k.png',True);heighttex.projection='BOX';heighttex.projection_blend=.28;nt.links.new(mapping.outputs[0],heighttex.inputs[0])
gb=nt.nodes.new('ShaderNodeBump');gb.inputs['Strength'].default_value=.5;gb.inputs['Distance'].default_value=.035;nt.links.new(heighttex.outputs[0],gb.inputs['Height']);nt.links.new(gb.outputs[0],p.inputs['Normal'])
# Fine rough bark without a large flattened stripe around a thin root.
nt=bark.node_tree;p=next(n for n in nt.nodes if n.type=='BSDF_PRINCIPLED')
for slot in ['Base Color','Normal']:
    for li in list(p.inputs[slot].links):nt.links.remove(li)
p.inputs['Base Color'].default_value=(.054,.036,.020,1);p.inputs['Roughness'].default_value=.88
nn=nt.nodes.new('ShaderNodeTexNoise');nn.inputs['Scale'].default_value=62;nn.inputs['Detail'].default_value=4
bm=nt.nodes.new('ShaderNodeBump');bm.inputs['Strength'].default_value=.35;bm.inputs['Distance'].default_value=.006;nt.links.new(nn.outputs['Fac'],bm.inputs['Height']);nt.links.new(bm.outputs[0],p.inputs['Normal'])
def center(y):return .9*math.sin(y*.22)+.04*max(y,0)
def height(x,y):
    side=x-center(y);d=abs(side);width=.90+.20*math.sin(y*.61+(1 if side<0 else 2))
    bank=(1.9 if side<0 else 1.4)*(1-math.exp(-max(0,d-width)**1.4*.85))
    broad=noise.noise_vector(Vector((x*.38,y*.34,2.7)))[0]
    fine=noise.noise_vector(Vector((x*3.3,y*3.3,3)))[1]
    return .030*(y+6)+bank+(.22+.3*min(bank,1))*broad+.055*fine+.22*math.sin(y*.31)*min(1,bank)
v=[];uv=[];faces=[];nx=250;ny=420
for j in range(ny+1):
    y=-10+j*48/ny
    for i in range(nx+1):
        x=-15+i*30/nx;v.append((x,y,height(x,y)));uv.append((x/2,y/2))
for j in range(ny):
    for i in range(nx):
        k=j*(nx+1)+i;faces.append((k,k+1,k+nx+2,k+nx+1))
ground=mesh('Eroded trail and asymmetric banks',v,faces,groundmat,'01 Terrain',uv)
tex=bpy.data.textures.new('Measured leaf litter height',type='IMAGE');tex.image=image(A/'forest_leaves_02/forest_leaves_02_disp_4k.png',True)
disp=ground.modifiers.new('Real relief / 18 millimetres','DISPLACE');disp.texture=tex;disp.texture_coords='UV';disp.strength=.018;disp.mid_level=.5
print('TERRAIN READY',flush=True)

sources={}
def import_models(asset,names=None):
    path=next((A/asset).glob('*.blend'))
    with bpy.data.libraries.load(str(path),link=False) as (src,dst):
        chosen=names or [n for n in src.objects if ('LOD0' in n or 'pine_roots' in n) and 'camera' not in n.lower()]
        dst.objects=[n for n in chosen if n in src.objects]
    result=[]
    for o in dst.objects:
        if o is None or o.type!='MESH':continue
        o.data=o.data.copy();o.data.transform(o.matrix_world);o.matrix_world=Matrix.Identity(4)
        o.parent=None
        for mod in list(o.modifiers):o.modifiers.remove(mod)
        if not o.data.uv_layers and 'UVMap' in o.data.attributes:
            vals=[tuple(q.vector[:2]) for q in o.data.attributes['UVMap'].data];o.data.attributes.remove(o.data.attributes['UVMap']);ly=o.data.uv_layers.new(name='UVMap')
            for k,q in enumerate(vals):ly.data[k].uv=q
        vv=[p.co for p in o.data.vertices]
        pivot=Vector(((min(q.x for q in vv)+max(q.x for q in vv))/2,(min(q.y for q in vv)+max(q.y for q in vv))/2,min(q.z for q in vv)))
        for q in o.data.vertices:q.co-=pivot
        o.hide_render=False;o.hide_viewport=False;o.hide_set(False)
        o['source']='https://polyhaven.com/a/'+asset;o['license']='CC0-1.0'
        result.append(o)
    # Source .blend files sometimes use a different relative texture root.
    for im in bpy.data.images:
        if im.source=='FILE' and not im.packed_file:
            candidate=A/asset/'textures'/Path(im.filepath.replace('\\','/')).name
            if candidate.exists():im.filepath=str(candidate)
    sources[asset]=result
    print('IMPORTED',asset,[(o.name,len(o.data.vertices)) for o in result],flush=True)
    return result
rocks=import_models('rock_moss_set_01',[f'rock_moss_set_01_rock{i:02}' for i in range(1,7)])
ferns=import_models('fern_02',[f'fern_02_{c}' for c in 'abcd'])
shrubs=import_models('shrub_04',[f'shrub_04_{c}_LOD0' for c in 'abcd'])
logs=import_models('dead_tree_trunk',['dead_tree_trunk'])
trees=import_models('fir_tree_01',[f'fir_tree_01_{c}_LOD1' for c in 'abc']+[f'fir_tree_01_trunk_{c}' for c in 'abc'])
roots=import_models('pine_roots')
moss=import_models('moss_01',['moss_01_a_LOD0','moss_01_b_LOD0','moss_01_c_LOD0'])
def place(src,x,y,z=None,s=1,rot=None,group='02 Hero rocks',name=None):
    o=src.copy();o.data=src.data;link(o,group);o.location=(x,y,height(x,y) if z is None else z)
    o.rotation_euler=rot if rot is not None else (0,0,r.random()*math.tau);o.scale=(s,s,s) if isinstance(s,(int,float)) else s
    if name:o.name=name
    return o
# Deliberately anchored major forms: alternating masses, never a repeated wall.
hero=[(-2.8,-3.3,1.1,3),(-2.55,.2,1.05,0),(-3.25,3.1,1.35,4),(2.95,-1.2,1.15,1),(3.3,3.7,1.15,3),(-2.7,7.2,.83,2),(3.65,9.3,.95,4),(-2.2,12.4,.85,1)]
rock_instances=[]
for i,(x,y,s,idx) in enumerate(hero):
    z=height(x,y)-.85
    o=place(rocks[idx],x,y,z,s,rot=(r.uniform(-.18,.18),r.uniform(-.2,.2),r.uniform(0,6.28)),name=f'Hero moss boulder {i:02}');rock_instances.append(o)
for i in range(96):
    y=r.uniform(-6,31);side=r.choice([-1,1]);x=center(y)+side*r.uniform(1.15,7.7);s=r.uniform(.15,.55)
    rock_instances.append(place(r.choice(rocks),x,y,height(x,y)-.2*s,s,rot=(r.uniform(-.2,.2),r.uniform(-.25,.25),r.random()*math.tau)))
for i in range(230):
    y=r.uniform(-7,30);x=center(y)+r.uniform(-1.15,1.15);s=r.uniform(.02,.15)
    place(r.choice(rocks),x,y,height(x,y)-.08*s,s,rot=(r.uniform(-.25,.25),r.uniform(-.25,.25),r.random()*math.tau),group='06 Leaf litter')
# Scanned tree silhouettes, lower trunks and irregular spacing.
treepos=[(-3.4,-1.8,1.04),(4.1,1.5,1.10),(-4.3,5.2,.88),(3.1,8.4,.8),(-3.6,13,.75),(4.7,15.6,.9)]
for i in range(54):
    y=r.uniform(-3,44);x=r.uniform(-16,16)
    if abs(x-center(y))>2.4:treepos.append((x,y,r.uniform(.48,1.12)))
for i,(x,y,s) in enumerate(treepos):
    src=trees[i%3]
    place(src,x,y,height(x,y)-.08,s,rot=(r.uniform(-.06,.06),r.uniform(-.06,.06),r.random()*math.tau),group='03 Forest trees')
    if y<18:
        for j in range(r.randint(1,3)):
            place(r.choice(roots),x+r.uniform(-.4,.4),y+r.uniform(-.4,.4),height(x,y)-.12,r.uniform(.8,1.4)*s,group='05 Roots and deadwood')
# Extend only the visible far tree line so the HDR panorama never supplies giant trunks.
for i in range(120):
    y=r.uniform(31,77);x=r.uniform(-31,31);place(trees[i%3],x,y,.9+(y-29)*.16,r.uniform(.55,1.05),group='03 Forest trees')
far=mesh('Distant forest floor',[(-100,29,.9),(100,29,.9),(100,250,36.26),(-100,250,36.26)],[(0,1,2,3)],groundmat,'01 Terrain',[(0,0),(100,0),(100,110),(0,110)])
# Far stems and crowns continue past the ground edge; the horizon stays occluded.
for i in range(280):
    y=r.uniform(70,195);x=r.uniform(-70,70)
    place(trees[i%3],x,y,.9+(y-29)*.16,r.uniform(.75,1.3),rot=(r.uniform(-.06,.06),r.uniform(-.06,.06),r.random()*6.28),group='03 Forest trees')
# Ferns collect near shade, crevices and trail edge; central footfall stays open.
for i in range(1350):
    y=r.uniform(-7,33);x=r.uniform(-9,9);d=abs(x-center(y))
    if d<.93 or (d>5 and r.random()<.5):continue
    s=r.uniform(.9,2.25)*(1 if y<20 else 1.1)
    place(r.choice(ferns),x,y,height(x,y)-.025,s,rot=(r.uniform(-.18,.18),r.uniform(-.18,.18),r.random()*math.tau),group='04 Ferns and understory')
for i in range(95):
    y=r.uniform(-5,33);x=center(y)+r.choice([-1,1])*r.uniform(2.2,9)
    for j in range(r.randint(5,11)):
        xx=x+r.uniform(-.55,.55);yy=y+r.uniform(-.55,.55)
        place(r.choice(shrubs),xx,yy,height(xx,yy),r.uniform(2.2,4.2),rot=(r.uniform(-.5,.5),r.uniform(-.5,.5),r.random()*math.tau),group='04 Ferns and understory')
# Dense regrowth closes the view at the bend and hides bare far-ground silhouettes.
for i in range(80):
    y=r.uniform(21,37);x=r.uniform(-11,11)
    for j in range(12):
        xx=x+r.uniform(-.7,.7);yy=y+r.uniform(-.7,.7)
        zz=max(height(xx,yy),.9+max(0,yy-29)*.16)
        place(r.choice(shrubs),xx,yy,zz,r.uniform(4,8),rot=(r.uniform(-.35,.35),r.uniform(-.35,.35),r.random()*6.28),group='04 Ferns and understory')
for x,y,s,idx in [(2.5,20,1.3,4),(.3,25,1.8,3),(-2.1,29,1.3,1)]:
    place(rocks[idx],x,y,height(x,y)-.35,s,group='02 Hero rocks')
# Young conifers form the intermediate woodland layer beneath the mature canopy.
for i in range(100):
    y=r.uniform(26,49);x=r.uniform(-18,18)
    zz=max(height(x,y),.9+max(0,y-29)*.16)
    place(trees[i%3],x,y,zz-.1,r.uniform(.22,.43),rot=(r.uniform(-.08,.08),r.uniform(-.08,.08),r.random()*math.tau),group='03 Forest trees')
# A broken log parallel to the bank, plus smaller fragments.
place(logs[0],2.8,-2.9,height(2.8,-2.9)-.05,1.1,rot=(.1,-.08,.72),group='05 Roots and deadwood',name='Foreground fallen branch / scanned')
place(logs[0],-2.05,5.7,height(-2.05,5.7),1.1,rot=(0,.13,1.07),group='05 Roots and deadwood')
for i in range(13):
    y=r.uniform(-4,26);x=center(y)+r.choice([-1,1])*r.uniform(1.3,5)
    place(logs[0],x,y,height(x,y)-.02,r.uniform(.25,.7),rot=(0,r.uniform(-.14,.14),r.random()*6.28),group='05 Roots and deadwood')

def tube(name,points,radii,mat,group,sides=7):
    vv=[];ff=[];uv=[];length=0
    for i,p in enumerate(points):
        p=Vector(p);t=Vector(points[min(i+1,len(points)-1)])-Vector(points[max(i-1,0)])
        t.normalize();axis=t.cross(Vector((0,0,1)))
        if axis.length<.01:axis=t.cross(Vector((0,1,0)))
        axis.normalize();other=t.cross(axis)
        if i:length+=(p-Vector(points[i-1])).length
        for j in range(sides):
            a=j*math.tau/sides;vv.append(p+(axis*math.cos(a)+other*math.sin(a))*radii[i]);uv.append((j/sides,length*.8))
    for i in range(len(points)-1):
        for j in range(sides):
            a=i*sides+j;b=i*sides+(j+1)%sides;ff.append((a,b,b+sides,a+sides))
    return mesh(name,vv,ff,mat,group,uv)
# Roots follow the bank, taper, and emerge / re-enter the terrain.
for i in range(135):
    y=r.uniform(-5,20);sgn=r.choice([-1,1]);x=center(y)+sgn*r.uniform(1.5,4.5);length=r.uniform(.4,2.3);pts=[];rr=[]
    rad=r.uniform(.012,.048)
    for j in range(9):
        t=j/8;xx=x-sgn*length*.5*t+.08*math.sin(t*8+i);yy=y+length*t
        pts.append((xx,yy,height(xx,yy)+.04+math.sin(t*math.pi)*r.uniform(.02,.07)));rr.append(rad*(1-.92*t))
    tube('Exposed tapering root',pts,rr,bark,'05 Roots and deadwood')
for j,y in enumerate([-2.1,1.4,4.3,8.5,12.2]):
    pts=[];rr=[]
    for k in range(19):
        t=k/18;xx=center(y)-1.8+3.8*t;yy=y+.35*math.sin(t*3.14)+.12*math.sin(t*9+j)
        pts.append((xx,yy,height(xx,yy)+.025+.025*math.sin(t*3.14)));rr.append(.043*(1-.8*t))
    tube('Old root crossing the trail',pts,rr,bark,'05 Roots and deadwood',11)
for i in range(450):
    y=r.uniform(-6,27);x=r.uniform(-6,6);a=r.random()*6.28;le=r.uniform(.04,.38);pts=[]
    for j in range(3):
        t=j/2;xx=x+math.cos(a)*le*t;yy=y+math.sin(a)*le*t;pts.append((xx,yy,height(xx,yy)+.025+(.018 if j==1 else 0)))
    tube('Dry twig',pts,[.006,.004,.0015],bark,'06 Leaf litter',5)
# Curled leaf silhouettes provide contact shadows that flat terrain maps cannot.
leafm=[]
for i,col in enumerate([(.12,.065,.025,1),(.21,.12,.052,1),(.09,.068,.036,1),(.28,.17,.075,1),(.15,.105,.057,1)]):
    ma=bpy.data.materials.new('Decaying leaf %d'%i);ma.use_nodes=True;p=ma.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=col;p.inputs['Roughness'].default_value=.72
    tex=ma.node_tree.nodes.new('ShaderNodeTexNoise');tex.inputs['Scale'].default_value=44;tex.inputs['Detail'].default_value=3
    bump=ma.node_tree.nodes.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.3;bump.inputs['Distance'].default_value=.0007;ma.node_tree.links.new(tex.outputs['Fac'],bump.inputs['Height']);ma.node_tree.links.new(bump.outputs[0],p.inputs['Normal']);leafm.append(ma)
vv=[];ff=[];inds=[]
for i in range(12500):
    y=r.uniform(-7,22);x=r.uniform(-7,7);d=abs(x-center(y))
    if d<.55 and r.random()<.55:continue
    a=r.random()*6.28;le=r.uniform(.025,.095);width=le*r.uniform(.25,.6);curl=r.uniform(.003,.018);z=height(x,y)+.012;base=len(vv)
    for j in range(5):
        t=j/4;w=math.sin(math.pi*t)*width
        for s in [-1,0,1]:
            dx=(t-.5)*le*2;dy=s*w;zz=z+curl*(abs(t-.5)*2)**2+(abs(s)*r.uniform(.001,.009))
            vv.append((x+math.cos(a)*dx-math.sin(a)*dy,y+math.sin(a)*dx+math.cos(a)*dy,zz))
    mi=r.randrange(len(leafm))
    for j in range(4):
        for k in range(2):q=base+j*3+k;ff.append((q,q+1,q+4,q+3));inds.append(mi)
ob=mesh('Curled and overlapping fallen leaves',vv,ff,None,'06 Leaf litter')
for ma in leafm:ob.data.materials.append(ma)
for p,i in zip(ob.data.polygons,inds):p.material_index=i
# Upper broadleaf branches break up the conifer canopy with real leaf silhouettes.
for i in range(160):
    x=r.uniform(-12,12);y=r.uniform(-3,35);z=r.uniform(6.2,12)
    if abs(x-center(y))<1.7 and 3<y<13 and r.random()<.70:continue
    for j in range(5):
        place(r.choice(shrubs),x+r.uniform(-.8,.8),y+r.uniform(-.8,.8),z+r.uniform(-.4,.4),r.uniform(4,7),rot=(r.uniform(-1.1,1.1),r.uniform(-1.1,1.1),r.random()*6.28),group='07 Canopy')
# Moss strands conform to upper surfaces of the foreground rocks through cached BVHs.
bpy.context.view_layer.update()
for rock in rock_instances[:8]:
    bvh=BVHTree.FromPolygons([v.co for v in rock.data.vertices],[p.vertices[:] for p in rock.data.polygons])
    inv=rock.matrix_world.inverted()
    mv=[];mf=[];muv=[];mindices=[]
    for j in range(750):
        xx=rock.location.x+r.uniform(-1.4,1.4)*rock.scale.x;yy=rock.location.y+r.uniform(-1.4,1.4)*rock.scale.y
        origin=Vector((xx,yy,rock.location.z+5));direction=(inv.to_3x3()@Vector((0,0,-1))).normalized()
        loc,norm,idx,dist=bvh.ray_cast(inv@origin,direction)
        if loc is not None and norm.z>.22 and noise.noise_vector(Vector((xx*3,yy*3,1)))[0]>.04:
            world=rock.matrix_world@loc;worldnorm=(rock.matrix_world.to_3x3().inverted().transposed()@norm).normalized()
            si=r.randrange(len(moss));src=moss[si];scale=r.uniform(.7,1.6);rot=worldnorm.to_track_quat('Z','Y').to_matrix();base=len(mv)
            mv.extend([world+rot@v.co*scale for v in src.data.vertices])
            for poly in src.data.polygons:
                mf.append(tuple(base+i for i in poly.vertices));mindices.append(si)
                for li in poly.loop_indices:muv.append(tuple(src.data.uv_layers.active.data[li].uv))
    if mv:
        mo=mesh('Living moss on '+rock.name,mv,mf,None,'04 Ferns and understory')
        for src in moss:mo.data.materials.append(src.data.materials[0])
        for p,mi in zip(mo.data.polygons,mindices):p.material_index=mi
        uv=mo.data.uv_layers.new(name='UVMap')
        for li,co in enumerate(muv):uv.data[li].uv=co
    print('MOSS PATCH',rock.name,len(mv),flush=True)

# Licensed Megascans decal: fade the scanned opacity into a smooth boundary.
qfolder=A/'megascans/moss'
if qfolder.exists():
    q=bpy.data.materials.new('Megascans | Tileable Moss Patches sfdnqii | 4K');q.use_nodes=True
    n=q.node_tree.nodes;l=q.node_tree.links;n.clear();out=n.new('ShaderNodeOutputMaterial');p=n.new('ShaderNodeBsdfPrincipled');l.new(p.outputs[0],out.inputs['Surface'])
    tc=n.new('ShaderNodeTexCoord');sep=n.new('ShaderNodeSeparateXYZ');l.new(tc.outputs['UV'],sep.inputs[0])
    alpha=None
    for ch,sock in [('BaseColor','Base Color'),('Roughness','Roughness'),('Opacity','Alpha'),('Normal','Normal')]:
        im=next(qfolder.glob('*_'+ch+'.jpg'));t=n.new('ShaderNodeTexImage');t.image=image(im,ch!='BaseColor');l.new(tc.outputs['UV'],t.inputs[0]);t.extension='CLIP'
        if ch=='Normal':
            nm=n.new('ShaderNodeNormalMap');nm.inputs[0].default_value=.55;l.new(t.outputs[0],nm.inputs['Color']);l.new(nm.outputs[0],p.inputs[sock])
        elif ch=='Opacity':alpha=t.outputs[0]
        else:l.new(t.outputs[0],p.inputs[sock])
    # Fade all four edges; multiplying the scan's opacity preserves organic holes.
    mask=alpha
    for axis in ['X','Y']:
        for op in ['GREATER_THAN','LESS_THAN']:
            edge=n.new('ShaderNodeMapRange');edge.clamp=True
            l.new(sep.outputs[axis],edge.inputs['Value']);edge.inputs['From Min'].default_value=.015 if op=='GREATER_THAN' else .82;edge.inputs['From Max'].default_value=.18 if op=='GREATER_THAN' else .985
            edge.inputs['To Min'].default_value=0 if op=='GREATER_THAN' else 1;edge.inputs['To Max'].default_value=1 if op=='GREATER_THAN' else 0
            mul=n.new('ShaderNodeMath');mul.operation='MULTIPLY';l.new(mask,mul.inputs[0]);l.new(edge.outputs[0],mul.inputs[1]);mask=mul.outputs[0]
    l.new(mask,p.inputs['Alpha'])
    # Triplanar scanned moss grows primarily on upper rock faces and broken patches.
    for rockmat in {m for ob in rocks for m in ob.data.materials if m}:
        nt=rockmat.node_tree;nn=nt.nodes;ll=nt.links
        output=next(n for n in nn if n.type=='OUTPUT_MATERIAL');old=output.inputs['Surface'].links[0].from_socket
        mossbs=nn.new('ShaderNodeBsdfPrincipled');mossbs.inputs['Roughness'].default_value=.82
        geo=nn.new('ShaderNodeNewGeometry');normal=nn.new('ShaderNodeSeparateXYZ');ll.new(geo.outputs['Normal'],normal.inputs[0])
        pos=nn.new('ShaderNodeVectorMath');pos.operation='SCALE';pos.inputs[3].default_value=.8;ll.new(geo.outputs['Position'],pos.inputs[0])
        color=nn.new('ShaderNodeTexImage');color.image=image(next(qfolder.glob('*_BaseColor.jpg')));color.projection='BOX';color.projection_blend=.3;ll.new(pos.outputs[0],color.inputs[0]);ll.new(color.outputs[0],mossbs.inputs['Base Color'])
        ntex=nn.new('ShaderNodeTexNoise');ntex.inputs['Scale'].default_value=2.5;ntex.inputs['Detail'].default_value=3;ll.new(geo.outputs['Position'],ntex.inputs[0])
        mul=nn.new('ShaderNodeMath');mul.operation='ADD';ll.new(ntex.outputs['Fac'],mul.inputs[0]);ll.new(normal.outputs['Z'],mul.inputs[1])
        ramp=nn.new('ShaderNodeMapRange');ramp.clamp=True;ramp.inputs['From Min'].default_value=.55;ramp.inputs['From Max'].default_value=1.15;ll.new(mul.outputs[0],ramp.inputs[0])
        btex=nn.new('ShaderNodeTexImage');btex.image=image(next(qfolder.glob('*_Bump.jpg')),True);btex.projection='BOX';btex.projection_blend=.25;ll.new(pos.outputs[0],btex.inputs[0])
        bm=nn.new('ShaderNodeBump');bm.inputs['Strength'].default_value=.55;bm.inputs['Distance'].default_value=.015;ll.new(btex.outputs[0],bm.inputs['Height']);ll.new(bm.outputs[0],mossbs.inputs['Normal'])
        opacity=nn.new('ShaderNodeTexImage');opacity.image=image(next(qfolder.glob('*_Opacity.jpg')),True);opacity.projection='BOX';opacity.projection_blend=.3;ll.new(pos.outputs[0],opacity.inputs[0])
        coverage=nn.new('ShaderNodeMath');coverage.operation='MULTIPLY';ll.new(ramp.outputs[0],coverage.inputs[0]);ll.new(opacity.outputs['Color'],coverage.inputs[1])
        mix=nn.new('ShaderNodeMixShader');ll.new(coverage.outputs[0],mix.inputs[0]);ll.new(old,mix.inputs[1]);ll.new(mossbs.outputs[0],mix.inputs[2]);ll.new(mix.outputs[0],output.inputs['Surface'])
    for i in range(36):
        y=r.uniform(-4.5,22);x=center(y)+r.choice([-1,1])*r.uniform(1.0,3.0);size=r.uniform(.45,1.45);ang=r.random()*math.tau
        vv=[];ff=[];uu=[];N=16
        for j in range(N+1):
            for k in range(N+1):
                dx=(k/N-.5)*size;dy=(j/N-.5)*size;xx=x+dx*math.cos(ang)-dy*math.sin(ang);yy=y+dx*math.sin(ang)+dy*math.cos(ang)
                vv.append((xx,yy,height(xx,yy)+.016));uu.append((k/N,j/N))
        for j in range(N):
            for k in range(N):
                a=j*(N+1)+k;ff.append((a,a+1,a+N+2,a+N+1))
        ob=mesh('Megascans moss decal %02d'%i,vv,ff,q,'01 Terrain',uu);ob['source']='https://www.fab.com/listings/a9a94514-dfba-43cb-92bc-c550d79b8d5d';ob['license']='Fab Standard License; external maps not redistributed'
print('SCATTER READY',len(bpy.data.objects),flush=True)
# Physically thin foliage: keep authored alpha and use gentle diffuse transmission.
for mat in bpy.data.materials:
    if not mat.use_nodes:continue
    if any(s in mat.name.lower() for s in ['fern','shrub','moss_01','twig']):
        nt=mat.node_tree
        for p in [n for n in nt.nodes if n.type=='BSDF_PRINCIPLED']:
            if 'Subsurface Weight' in p.inputs:p.inputs['Subsurface Weight'].default_value=.035
            p.inputs['Roughness'].default_value=.58
            if 'Diffuse Transmission Weight' in p.inputs:p.inputs['Diffuse Transmission Weight'].default_value=.18
scene.world=bpy.data.worlds.new('Forest sky | measured HDR environment');scene.world.use_nodes=True
n=scene.world.node_tree.nodes;l=scene.world.node_tree.links;n.clear()
out=n.new('ShaderNodeOutputWorld');bg=n.new('ShaderNodeBackground');bg.inputs[1].default_value=.85
env=n.new('ShaderNodeTexEnvironment');env.image=image(A/'forest_slope/forest_slope_4k.hdr')
tc=n.new('ShaderNodeTexCoord');mp=n.new('ShaderNodeMapping');mp.inputs['Rotation'].default_value[2]=1.5
l.new(tc.outputs['Generated'],mp.inputs[0]);l.new(mp.outputs[0],env.inputs[0])
cool=n.new('ShaderNodeVectorMath');cool.operation='MULTIPLY';cool.inputs[1].default_value=(.78,.91,1.06);l.new(env.outputs[0],cool.inputs[0]);l.new(cool.outputs[0],bg.inputs[0])
skybg=n.new('ShaderNodeBackground');skybg.inputs[0].default_value=(.45,.57,.69,1);skybg.inputs[1].default_value=.8
lp=n.new('ShaderNodeLightPath');mix=n.new('ShaderNodeMixShader');l.new(lp.outputs['Is Camera Ray'],mix.inputs[0]);l.new(bg.outputs[0],mix.inputs[1]);l.new(skybg.outputs[0],mix.inputs[2]);l.new(mix.outputs[0],out.inputs['Surface'])
sun=bpy.data.lights.new('Late morning sunlight','SUN');sun.energy=1.8;sun.angle=math.radians(.65);sun.color=(1,.97,.9)
so=link(bpy.data.objects.new('Sun through canopy',sun),'08 Lighting');so.rotation_euler=Vector((-5,-3,-9)).to_track_quat('-Z','Y').to_euler()
# Subtle aerial perspective only beyond the foreground, not a curtain over the detail.
vm=bpy.data.materials.new('Distant air / subtle depth');vm.use_nodes=True;vn=vm.node_tree.nodes;vn.clear();vo=vn.new('ShaderNodeOutputMaterial');vs=vn.new('ShaderNodeVolumeScatter');vs.inputs['Density'].default_value=.0025;vs.inputs['Anisotropy'].default_value=.18;vm.node_tree.links.new(vs.outputs[0],vo.inputs['Volume'])
bpy.ops.mesh.primitive_cube_add(size=1,location=(0,44,12));fog=bpy.context.object;fog.name='Aerial perspective behind the near trees';fog.scale=(85,75,35);fog.data.materials.append(vm)
for c in list(fog.users_collection):c.objects.unlink(fog)
COL['08 Lighting'].objects.link(fog)
cam=bpy.data.cameras.new('Full frame 32mm');co=link(bpy.data.objects.new('Camera | woodland trail',cam),'09 Camera');co.location=(-.10,-4.7,1.48)
target=Vector((.60,9,2.05));co.rotation_euler=(target-co.location).to_track_quat('-Z','Y').to_euler();cam.lens=32;cam.sensor_width=36
cam.dof.use_dof=True;cam.dof.focus_distance=10;cam.dof.aperture_fstop=8;cam.dof.aperture_blades=9;cam.clip_end=180;scene.camera=co
scene.render.engine='CYCLES';scene.cycles.samples=512;scene.cycles.use_adaptive_sampling=True;scene.cycles.adaptive_threshold=.007;scene.cycles.adaptive_min_samples=48
scene.cycles.use_denoising=True;scene.cycles.denoiser='OPENIMAGEDENOISE';scene.cycles.max_bounces=10;scene.cycles.diffuse_bounces=4;scene.cycles.glossy_bounces=4;scene.cycles.transmission_bounces=6;scene.cycles.transparent_max_bounces=24
scene.cycles.sample_clamp_indirect=6;scene.cycles.use_light_tree=True
prefs=bpy.context.preferences.addons['cycles'].preferences
try:
    prefs.compute_device_type='OPTIX';prefs.get_devices()
    for d in prefs.devices:d.use=d.type=='OPTIX'
    scene.cycles.device='GPU'
except Exception as e:print('GPU setup',e)
scene.render.resolution_x=2400;scene.render.resolution_y=1600;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGB';scene.render.image_settings.color_depth='16';scene.render.film_transparent=False
scene.view_settings.view_transform='AgX';scene.view_settings.look='AgX - Medium High Contrast';scene.view_settings.exposure=.40
scene.render.filepath=str(ROOT/'renders/forest_path.png');scene.render.use_file_extension=True
scene['design']='A humid woodland footpath, composed for this one camera. Metres. Scanned materials and instanced flora.'
scene['asset_policy']='CC0 assets sourced from Poly Haven. See docs/ASSETS.md for additional licensed sources.'
# Remove unused source objects and resolve every external image relative to the saved scene.
for obs in sources.values():
    for ob in obs:
        if ob.users==0:bpy.data.objects.remove(ob)
for im in bpy.data.images:
    if im.source=='FILE' and not im.packed_file:
        absolute=Path(bpy.path.abspath(im.filepath))
        if not absolute.exists():
            matches=list(A.rglob(Path(im.filepath.replace('\\','/')).name))
            if matches:im.filepath=str(matches[0])
for area in bpy.context.screen.areas:
    if area.type=='VIEW_3D':
        area.spaces.active.region_3d.view_perspective='CAMERA';area.spaces.active.shading.type='MATERIAL'
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'scenes/ForestPath.blend'),compress=True)
bpy.ops.file.make_paths_relative()
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'scenes/ForestPath.blend'),compress=True)
if args.preview:
    scene.render.resolution_percentage=42;scene.cycles.samples=64;scene.cycles.adaptive_threshold=.035;scene.cycles.adaptive_min_samples=16
    scene.render.filepath=str(ROOT/'renders/preview_09.png')
bpy.ops.render.render(write_still=True)
print('FOREST_RENDER_COMPLETE',flush=True)
