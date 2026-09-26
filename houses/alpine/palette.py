"""Procedural architectural palette; real-world scale, no external texture dependency."""
import bpy
from archviz import materials as m

def painting(name,colors,vertical=False):
    mat,nt,b=m._new(name)
    tc=nt.nodes.new('ShaderNodeTexCoord')
    vec=m._coords(nt,scale=(.65,1,4.5) if not vertical else (2.8,1,.65))
    n=m._noise(nt,vec,scale=1.1,detail=7,rough=.72,distortion=.55)
    col=m._ramp(nt,m._stretch(nt,n,.31,.69),[(i/(len(colors)-1),(*c,1)) for i,c in enumerate(colors)])
    nt.links.new(b.inputs['Base Color'],col)
    b.inputs['Roughness'].default_value=.83
    fine=m._noise(nt,m._coords(nt,scale=(95,95,95)),scale=1,detail=2)
    m._bump(nt,b,fine,.13,.001)
    return mat

def rug(name,base,pattern):
    mat,nt,b=m._new(name)
    tc=nt.nodes.new('ShaderNodeTexCoord');sp=nt.nodes.new('ShaderNodeSeparateXYZ');nt.links.new(sp.inputs[0],tc.outputs['Generated'])
    x=m._math(nt,'SUBTRACT',sp.outputs['X'],.5);y=m._math(nt,'SUBTRACT',sp.outputs['Y'],.5)
    ax=m._math(nt,'ABSOLUTE',x);ay=m._math(nt,'ABSOLUTE',y)
    edge=m._math(nt,'MAXIMUM',ax,ay)
    border=m._math(nt,'MULTIPLY',m._math(nt,'GREATER_THAN',edge,.39),m._math(nt,'LESS_THAN',edge,.475))
    wave1=m._math(nt,'SINE',m._math(nt,'MULTIPLY',x,115))
    wave2=m._math(nt,'SINE',m._math(nt,'MULTIPLY',y,150))
    florets=m._math(nt,'GREATER_THAN',m._math(nt,'MULTIPLY',wave1,wave2),.52)
    fine=m._noise(nt,m._coords(nt,scale=(130,130,130)),scale=1,detail=2)
    worn=m._noise(nt,tc.outputs['Generated'],scale=58,detail=3)
    mask=m._math(nt,'MULTIPLY',m._math(nt,'MAXIMUM',border,florets),m._math(nt,'GREATER_THAN',worn,.43))
    col=m._mixrgb(nt,mask,(*base,1),(*pattern,1))
    nt.links.new(b.inputs['Base Color'],col);b.inputs['Roughness'].default_value=.95;b.inputs['Sheen Weight'].default_value=.45
    m._bump(nt,b,fine,.2,.003)
    return mat

def build():
    M={}
    M['brick']=m.tiles('Alpine | aged red brick',(.30,.105,.066,1),grout=(.37,.30,.235,1),size=(.235,.075),gap=.007,rough=.8,plane='XZ',variation=.28,mottle=.32,bump=.35,offset=.5)
    M['brick_y']=m.tiles('Alpine | side brick',(.30,.105,.066,1),grout=(.37,.30,.235,1),size=(.235,.075),gap=.007,rough=.8,plane='YZ',variation=.28,mottle=.32,bump=.35,offset=.5)
    M['paver']=m.tiles('Alpine | fired brick paving',(.31,.12,.075,1),grout=(.24,.21,.18,1),size=(.23,.105),gap=.007,rough=.68,variation=.22,mottle=.23,bump=.3,offset=.5)
    M['slate']=m.tiles('Alpine | slate shingle courses',(.13,.145,.17,1),grout=(.065,.07,.08,1),size=(.33,.19),gap=.005,rough=.82,variation=.35,mottle=.35,bump=.28,offset=.5)
    M['white']=m.plaster('Alpine | warm white plaster',(.83,.815,.76,1),grain=.025)
    M['trim']=m.new_mat('Alpine | ivory painted joinery',(.86,.84,.775,1),rough=.29,coat=.18)
    M['ceiling']=m.new_mat('Alpine | ceiling',(.88,.86,.81,1),rough=.82)
    M['shutter']=m.wood('Alpine | slate blue shutters',light=(.155,.215,.235,1),dark=(.09,.135,.15,1),rough=.47,coat=.18)
    M['oak']=m.wood('Alpine | library honey oak',light=(.46,.285,.14,1),dark=(.28,.15,.061,1),rough=.38,coat=.25)
    M['walnut']=m.wood('Alpine | polished walnut',light=(.057,.024,.009,1),dark=(.012,.006,.003,1),grain_axis='X',rough=.24,coat=.5)
    M['floor']=m.wood_planks('Alpine | dark wide oak',light=(.050,.021,.008,1),dark=(.008,.003,.001,1),plank=(2.2,.19),along='Y',rough=.28,coat=.28,gap=.0015)
    M['limestone']=m.tiles('Alpine | honed cream limestone',(.57,.49,.37,1),grout=(.50,.435,.335,1),size=(.9,.9),gap=.002,rough=.44,variation=.055,mottle=.16,bump=.08)
    M['counter']=m.noise_mat('Alpine | champagne granite',(.51,.405,.255,1),(.74,.65,.48,1),scale=160,rough=.22,bump=.05,bump_dist=.001)
    M['marble']=m.marble('Alpine | vanity marble',base=(.84,.82,.75,1),vein=(.47,.47,.43,1),vein2=(.66,.63,.57,1),rough=.2)
    for key,col,rough,metal in [('black',(.017,.021,.02),.32,.5),('brass',(.57,.36,.12),.25,1),('steel',(.57,.59,.6),.24,1),('mirror',(.94,.94,.94),.012,1),('porcelain',(.87,.86,.81),.16,0),('soil',(.055,.037,.023),.99,0)]:
        M[key]=m.new_mat('Alpine | '+key,(*col,1),rough=rough,metal=metal)
    M['glass']=m.new_mat('Alpine | clear glazing',(.96,.98,.97,1),rough=.02,transmission=1,ior=1.46)
    M['lamp']=m.new_mat('Alpine | warm lamp',(.9,.76,.50,1),rough=.5,emit=(1,.77,.43,1),emit_str=2.7)
    M['skylight']=m.new_mat('Alpine | diffuse rooflight',(.81,.86,.9,1),rough=.6,emit=(.88,.94,1,1),emit_str=.65)
    M['linen']=m.linen('Alpine | ivory linen',(.81,.79,.71,1),wrinkle=.2)
    M['blue']=m.fabric('Alpine | deep slate textile',(.065,.115,.145,1),weave=100)
    M['sage']=m.fabric('Alpine | olive linen',(.205,.24,.13,1))
    M['blush']=m.fabric('Alpine | blush boucle',(.58,.38,.3,1),weave=90)
    M['rug']=rug('Alpine | antique Persian carpet',(.40,.22,.125),(.71,.625,.43))
    M['rug_pale']=rug('Alpine | faded ivory carpet',(.63,.56,.43),(.42,.46,.34))
    M['runner']=m.rug('Alpine | striped stair runner',(.155,.16,.15,1),(.4,.40,.36,1),scale=95)
    M['turf']=m.turf('Alpine | lawn',c_dark=(.042,.11,.023,1),c_light=(.12,.22,.042,1))
    M['grass']=m.grass_blade('Alpine | grass blades',stripes=False,root=(.035,.075,.009,1),tip=(.19,.3,.045,1))
    M['gravel']=m.noise_mat('Alpine | fine limestone gravel',(.37,.36,.29,1),(.65,.61,.50,1),scale=95,bump=.28,bump_dist=.012)
    M['pool']=m.tiles('Alpine | pool mosaic',(.055,.19,.23,1),grout=(.08,.18,.19,1),size=(.035,.035),gap=.001,rough=.24,variation=.3,mottle=.05,bump=.08)
    M['water']=m.water('Alpine | still rippling water',tint=(.66,.86,.91,1),density=.12,ripple=.005,scatter=.005)
    M['fire']=m.new_mat('Alpine | ember flame',(.5,.12,.015,1),rough=.8,emit=(1,.32,.025,1),emit_str=1.7)
    M['art_sea']=painting('Alpine | tidal study',[(.69,.74,.63),(.47,.65,.55),(.18,.40,.37),(.065,.20,.2),(.33,.49,.44),(.78,.75,.6)])
    M['art_gold']=painting('Alpine | mineral study',[(.085,.11,.10),(.22,.265,.23),(.6,.56,.35),(.8,.76,.59),(.44,.47,.39),(.84,.81,.7)],True)
    M['art_rose']=painting('Alpine | warm abstract',[(.07,.11,.16),(.1,.28,.36),(.54,.2,.09),(.72,.42,.22),(.87,.78,.58)],True)
    for key,file in (('rug','rug_rust.png'),('rug_pale','rug_ivory.png')):
        from pathlib import Path
        mat=M[key];nt=mat.node_tree;b=nt.nodes.get('Principled BSDF')
        tex=nt.nodes.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(str(Path(__file__).parent/'assets'/file));tex.image.pack()
        tc=nt.nodes.new('ShaderNodeTexCoord');nt.links.new(tex.inputs['Vector'],tc.outputs['Generated']);nt.links.new(b.inputs['Base Color'],tex.outputs['Color'])
    return M
