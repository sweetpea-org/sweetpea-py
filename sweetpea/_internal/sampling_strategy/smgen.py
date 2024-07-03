from sweetpea._internal.sampling_strategy.base import Gen, SamplingResult
from sweetpea._internal.block import Block
from sweetpea._internal.primitive import *
from sweetpea._internal.constraint import *
from sweetpea._internal.sampling_strategy.scattered_map_core import (
    _Factor, _DerivedLevel, _WithinTrial, _Transition,
    encode_experiment, define_cross, execute, print_factors
)

'''
    ScatteredMap wrapper class to extract necessary information to
    run the main module.
'''

def _cexit(m,*var):
    if len(var)>0:
        for e in var:
            m+= " " + str(e)
    raise Exception(m)

class SMGen(Gen):
    @staticmethod
    def class_name():
        return 'SMGen'

    @staticmethod
    def sample(block: Block, sample_count: int) -> SamplingResult:
        print("In SMGen")

        if len(block.orig_crossings)>1:
            _cexit("CrossBlock() not called.")

        for c in block.constraints:
            if type(c)==AtMostKInARow or type(c)==AtLeastKInARow :
                _cexit("AtMost/AtLeast constraints not supported for this generator.")


        design=block.orig_design
        crossing=block.orig_crossings[0]
        primary=[]
        derived=[]
        p_dc={}
        dr_dc={}
        sm_design=[]
        sm_cross=[]
        for f in design:
            name=f.name
            levels=f.levels

            _levels=[]

            d_type=None

            if isinstance(levels[0],DerivedLevel):
                for l in levels:
                    ll=l.window
                    f=ll.predicate

                    if d_type==None:
                        if isinstance(ll,Transition):
                            d_type="tr"
                        elif isinstance(ll,WithinTrial):
                            d_type="wt"
                        else:
                            _cexit("Unsupported level",l.name)

                    args=ll.factors[:]

                    for i in range(len(args)):
                        args[i]=args[i].name

                    _levels.append([l.name,f,args,l._weight])
            else:
                for l in levels:
                    _levels.append(l.name)

            if d_type==None:
                primary.append([name,_levels])
            else:
                derived.append([name,_levels,d_type])


        for f in primary:
            p_dc[f[0]]=_Factor(f[0],f[1])


        for f in derived:
            sm_levels=[]
            if f[2]=="tr":
                continue
            for l in f[1]:
                args=l[2]
                for i in range(len(args)):
                    if args[i] in p_dc:
                        args[i]=p_dc[args[i]]

                sm_levels.append(_DerivedLevel(l[0],_WithinTrial(l[1],l[2]),l[3]))

            dr_dc[f[0]]=_Factor(f[0],sm_levels)

        for f in derived:
            sm_levels=[]
            if f[2]=="wt":
                continue
            for l in f[1]:
                args=l[2]
                for i in range(len(args)):
                    if args[i] in p_dc:
                        args[i]=p_dc[args[i]]
                    else:
                        args[i]=dr_dc[args[i]]

                sm_levels.append(_DerivedLevel(l[0],_Transition(l[1],l[2]),l[3]))


            dr_dc[f[0]]=_Factor(f[0],sm_levels)

        for f in design:
            if isinstance(f.levels[0],DerivedLevel):
                sm_design.append(dr_dc[f.name])
            else:
                sm_design.append(p_dc[f.name])

        for f in crossing:
            if isinstance(f.levels[0],DerivedLevel):
                sm_cross.append(dr_dc[f.name])
            else:
                sm_cross.append(p_dc[f.name])

        encode_experiment(sm_design)
        #print_factors()

        cross=define_cross(sm_cross)
        r=execute(answers_count=sample_count)

        samples=SamplingResult(r,{})

        return samples

