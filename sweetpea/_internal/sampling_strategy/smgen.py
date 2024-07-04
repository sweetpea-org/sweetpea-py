from sweetpea._internal.sampling_strategy.base import Gen, SamplingResult
from sweetpea._internal.block import Block
from sweetpea._internal.cross_block import CrossBlock
from sweetpea._internal.primitive import *
from sweetpea._internal.constraint import *
from sweetpea._internal.sampling_strategy.scattered_map_core import (
    _Factor, _DerivedLevel, _WithinTrial, _Transition,
    encode_experiment, define_cross, execute, print_factors,
    reset_state
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
        # print("In SMGen")
        assert(isinstance(block, MultiCrossBlockRepeat))

        if block.within_block_count != block.trials_per_sample():
            _cexit(f"Repeated blocks are not supported by SMGen.")
        if len(block.crossings) != 1:
            _cexit(f"Multiple-crossing blocks are not supported by SMGen.")

        for c in block.constraints:
            if (isinstance(c, AtMostKInARow) or isinstance(c, AtLeastKInARow) or isinstance(c, ExactlyK)
                or isinstance(c, Exclude) or isinstance(c, Pin)):
                _cexit(f"{type(c).__name__} constraints are not supported by SMGen.")

        # For now, implement a minimum-trials contraint by weighting the levels of
        # one non-derived factor
        maximum_trials = False
        scale_one = block.crossing_weight()
        if scale_one > 1:
            maximum_trials = block.trials_per_sample()

        reset_state()
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

            _levels=cast(List[object], [])

            d_type=None

            if isinstance(levels[0],DerivedLevel):
                for l in levels:
                    assert(isinstance(l, DerivedLevel))
                    ll=l.window
                    pred=ll.predicate

                    if d_type==None:
                        if isinstance(ll,Transition):
                            d_type="tr"
                        elif isinstance(ll,WithinTrial):
                            d_type="wt"
                        else:
                            _cexit("Unsupported level", l.name)

                    args=ll.factors[:]

                    arg_names=[]
                    for i in range(len(args)):
                        arg_names.append(args[i].name)

                    _levels.append([l.name,pred,arg_names,l._weight])
            else:
                # For now, implement weighting for a non-derived factor by duplicating levels
                for l in levels:
                    for i in range(scale_one * l._weight):
                        _levels.append(l.name)
                scale_one = 1

            if d_type==None:
                primary.append([name,_levels])
            else:
                derived.append([name,_levels,d_type])


        for fp in primary:
            p_dc[fp[0]]=_Factor(fp[0],fp[1])


        for fd in derived:
            sm_levels=[]
            if fd[2]=="tr":
                continue
            for ld in cast(List, fd[1]):
                args=ld[2]
                for i in range(len(args)):
                    if args[i] in p_dc:
                        args[i]=p_dc[args[i]] # type: ignore

                sm_levels.append(_DerivedLevel(ld[0],_WithinTrial(ld[1],ld[2]),ld[3]))

            dr_dc[fd[0]]=_Factor(fd[0],sm_levels)

        for fd in derived:
            sm_levels=[]
            if fd[2]=="wt":
                continue
            for ld in cast(List, fd[1]):
                args=ld[2]
                for i in range(len(args)):
                    if args[i] in p_dc:
                        args[i]=p_dc[args[i]] # type: ignore
                    else:
                        args[i]=dr_dc[args[i]] # type: ignore

                sm_levels.append(_DerivedLevel(ld[0],_Transition(ld[1],ld[2]),ld[3]))


            dr_dc[fd[0]]=_Factor(fd[0],sm_levels)

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
        r=execute(answers_count=sample_count, maximum_trials=maximum_trials)

        samples=SamplingResult(r,{})

        return samples

