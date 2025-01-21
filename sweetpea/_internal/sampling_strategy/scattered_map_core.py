'''
    < Scattered Map > generator.

    We shrink the sample-space toward valid answers and use directed branching
    to target combinations that comply with user-defined constraints.
    A completed permutation in this strategy is not rejected. When a permutation is
    fully created, it is gauaranteed that:
      1- The cross is valid.
      2- The transitions are valid. Meaning each pair of two consecutive
         combinations fullfills all the defined transitional constraints.

    The core algorithm thresholds play an important role in how efficiently a
    permutation can be completed. The thresholds should dynamically change for
    each experiment as there is not an ideal number for all cases.
    The default time-out is 60 seconds which should be more than enough for
    most normal experiments. If thresholds are configured correctly, the algorithm
    should find a correct answer within a few seconds.

    By Sirus Shahini
    ~cyn

'''

from random import random
from time import time
# from signal import signal,setitimer,ITIMER_REAL,SIGALRM

# from signal import signal,setitimer,ITIMER_REAL,SIGALRM
import threading

# Module global variables
##########################################################
objects=[]
primary_objects=[]
transitions=[]
within_trials=[]

cross=[]

weighted_objects=[]
weights=[]
weighted_objects_init=[]
weights_init=[]
wt_count=0
trans_count=0
c_counts = []
c_objs_count=0
trans_cells=[]
trans_cell_start=-1
wt_cells=[]
obs_counts=[]
comb_len =0
all_weights=[]
cross_weights=[]
cross_counts=[]
unweighted_experiment=True
M=0
M_raw=0
L=0
asg_vf={}
asg_wt_vf={}

EXEC_TH=60
##########################################################

def reset_state():
    global objects, primary_objects, transitions, within_trials, cross, weighted_objects, weights
    global weighted_objects_init, weights_init, wt_count, trans_count, c_counts, c_objs_count
    global trans_cells, trans_cell_start, wt_cells, obs_counts, comb_len, all_weights, cross_weights
    global cross_counts, unweighted_experiment, M, M_raw, L, asg_vf, asg_wt_vf, EXEC_TH
    
    objects=[]
    primary_objects=[]
    transitions=[]
    within_trials=[]
    
    
    cross=[]
    
    weighted_objects=[]
    weights=[]
    weighted_objects_init=[]
    weights_init=[]
    wt_count=0
    trans_count=0
    c_counts = []
    c_objs_count=0
    trans_cells=[]
    trans_cell_start=-1
    wt_cells=[]
    obs_counts=[]
    comb_len =0
    all_weights=[]
    cross_weights=[]
    cross_counts=[]
    unweighted_experiment=True
    M=0
    M_raw=0
    L=0
    asg_vf={}
    asg_wt_vf={}
    
    EXEC_TH=60    

def _cexit(m,*var):
    if len(var)>0:
        for e in var:
            m+= " " + str(e)
    raise Exception(m)

def shuffle_list(l):
    if len(l)==1:
        return

    for i in range(len(l)-1,-1,-1):
        ind=int(random()*len(l))

        tmp=l[ind]
        l[ind]=l[i]
        l[i]=tmp

'''
    Calculate the direct index of the combination within the space of
    the possible combinaitons in the cross.
'''
def comb_index(combs):
    right_cross=1
    r=0
    for i in range(len(cross)-1,-1,-1):
        if combs[cross[i]] >= cross_counts[i] : _cexit("invalid input")
        r += combs[cross[i]] * right_cross
        right_cross*=cross_counts[i]

    return r

'''
    Return the number of necessary copies of a given combination based on
    the weights config.
    We use the structures that we populate in the execute function to find the correct
    number. The generation of a given combination is halted when we hit the cap that
    is returned by this function.
'''
def get_cap(comb):
    if unweighted_experiment:
        return 1

    r=1
    for i in range(len(weighted_objects)):
        w_obj = weighted_objects[i][0]
        val=comb[w_obj]

        for j in range(len(weighted_objects[i])-1):
            weighted_level_ind=weighted_objects[i][j+1]
            if val == weighted_level_ind:
                r *= all_weights[w_obj][weighted_level_ind]
                break

    return r

'''
    Return the number of cells that we need to fill to create a cross
    based on the user constraints. This is an init function and the use
    of sum() is fine here.
'''
def perms_count(raw):
    r=1

    if unweighted_experiment or raw:
        for i in range(len(cross_counts)):
            r*=cross_counts[i]
    else:
        for i in range(len(cross_counts)):
            r*= sum(cross_weights[i])

    return r

'''
    Return a fresh row strcuture to the back-tracking function.
'''
def new_rows(w):
    rows=[]
    for i in range(w):
        r=[0]*c_objs_count
        r[-1]=-1
        rows.append(r)
    return rows

def clear_single_row(ar):
    for i in range(c_objs_count-1):
        ar[i]=0
    ar[-1]=-1

'''
    Clear object tracker to init the next round of permutation generation.
'''
def clear_nums(nums):
    for i in range(M_raw):
        nums[i][0]=0
        if unweighted_experiment:
            clear_single_row(nums[i][1][0])
        else:
            for j in range(len(nums[i][1])):
                clear_single_row(nums[i][1][j])

'''
    Return the current active object for combination "ind" that
    we are enumerating possible transitions to the neighboring cell.
'''
def get_states_ar_ind(nums,ind):
    if nums[ind][0]<1:
        _cexit("Invalid get state request")

    return nums[ind][0]-1

'''
    This is the core algorithm of this module. This algorithm randomly branches to a valid
    combination for the cell to its right. It stops progression of the path by early detection
    of the first cell that creates an invalid derived factor. A big number of paths that end up
    in invalid permutations from the sample space are avoided. For a partial path of length l
    that is discarded, (M-l)! permutations are eliminated from the sample space.
    When we get to fill the last cell, a valid cross is guaranteed.
    The algorithm does not depend on the sepcific characteristics of the default model that I have
    assumed for the objects. As long as you can clearly define what you want the code
    to look back and forward to form the basis of a "valid" next combination, it will
    work to create a correct permutation for sweetpea experiments. For example, the current
    code assumes that the window size for a Transition derived level is 2, meaning that we pass
    the previous and the next values of the respective factor to know that which predicate
    function is chosen. The window size can be larger, but it does need updating the code
    to adapt to the new expectation.
'''
def sm_backtrack_random():
    permut=[]
    nums=[]

    for i in range(M):
        line = [-1] * comb_len
        permut.append(line)

    weight=1
    for i in range(M_raw):
        if not unweighted_experiment:
            weight=combs_weights[i]

        nums.append([0 , new_rows(weight)  ])


    back_steps=0
    total_bck=0

    '''
        Chossing these threasholds needs more work.
        SM_CORE_TH changes dynamically.
        When an experiment starts to get problematic, we generally benefit from
        reducing SM_CORE_TH to smaller numbers (like 30-40). But for most difficult
        experiments 100-150 works overall better.
        Generally, if we choose something tens of units greater or smaller than the
        ideal threashold for the current experiment, efficiency is notably hurt.

    '''
    SM_CORE_TH_MIN=100
    SM_CORE_TH_RNG=100
    SM_CORE_TH_RET=150
    SM_CORE_TH_MAX=150
    SM_CORE_TH=SM_CORE_TH_MAX

    loc=0
    pre=[]

    '''
        Main loops.
        Outer loop: Start with forming the initial states and take it from there.
        Each group of factors are handled separately. We enumerate through the primary
        objects and then fill the dependent cells which are WithinTrials and Transitions.
        The primary target cells constitute the main elements of the back-tracking logic.
        Note that the value for a dependent cell is looked up in O(1) using the init maps
        instead on actually calling the predicate functions.
        We reference the nums structure to track the objects in combination selection process.
    '''
    while True:

        for i in range(c_objs_count):
            permut[0][i]=int(random()* obs_counts[i])

        if trans_count>0:
            pre=[-1]*(c_objs_count + wt_count)
            for i in range(c_objs_count):
                pre[i]=int(random()* obs_counts[i])
            for i in range(wt_count):
                wt=within_trials[i]
                wt_id=wt_cells[i][0]
                params=[]
                for ind in wt_cells[i][1]:
                    params.append(pre[ind])

                ans=get_wt_val(asg_wt_vf[i],params)
                pre[wt_id]=ans

                params=[]
                for ind in wt_cells[i][1]:
                    params.append(permut[0][ind])

                ans=get_wt_val(asg_wt_vf[i],params)
                permut[0][wt_id]=ans

            for i in range(trans_count):
                target_cell=trans_cells[i][1]
                trans_ind=trans_cells[i][0]

                src=pre[target_cell]
                dst=permut[0][target_cell]

                ans=(asg_vf[i])[src][dst]
                permut[0][trans_ind]=ans

        else:
            for i in range(wt_count):
                #just permut[0]

                wt=within_trials[i]
                wt_id=wt_cells[i][0]

                params=[]
                for ind in wt_cells[i][1]:
                    params.append(permut[0][ind])

                ans=get_wt_val(asg_wt_vf[i],params)
                permut[0][wt_id]=ans


        '''
        for i in range(c_objs_count,comb_len):
            ans=(asg_vf[i-c_objs_count])[  pre[i-c_objs_count]  ][ permut[0][i-c_objs_count]  ]
            permut[0][i]=ans
        '''

        comb = comb_index(permut[0])
        nums[comb][0]=1

        loc=0
        back_steps=0
        #print("[>] Exec JUMP",permut[0],comb)

        rand_asg=[] #each time create a new assignment
        for i in range(M):
            line=[]

            for j in range(c_objs_count):
                obj=[]
                for z in range(c_counts[j]):
                    obj.append(z)
                shuffle_list(obj)
                line.append(obj)

            rand_asg.append(line)

        '''
            Inner loop: Choose a random valid path to right. In each step
            a whole combination is formed and stored at the next cell. If the
            current cell fails, revert to previous cell and choose another available
            path.
        '''
        while 1:
            if loc==L-1:
                return pre,permut
            elif loc==-1:
                clear_nums(nums)
                break

            right_ind=comb_index(permut[loc])
            if unweighted_experiment:
                c_states = nums[right_ind][1][ 0 ]
            else:
                c_states = nums[right_ind][1][ get_states_ar_ind(nums,right_ind) ]

            c_states[-1] += 1
            for i in range(c_objs_count-1,0,-1):
                if c_states[i] > c_counts[i]:
                    _cexit("invalid c states")

                if c_states[i] == c_counts[i]:
                    c_states[i]=0
                    c_states[i-1] += 1

            if c_states[0] == c_counts[0]:
                nums[right_ind][0] -= 1
                #permut[loc]=-1

                loc-=1
                back_steps+=1
                total_bck+=1

                if back_steps>SM_CORE_TH:
                    clear_nums(nums)

                    if SM_CORE_TH > SM_CORE_TH_MIN:
                        SM_CORE_TH -= 1
                    else:
                        SM_CORE_TH=SM_CORE_TH_RET

                    break

                continue

            new_comb=[-1]*comb_len

            if unweighted_experiment:
                c_objs=nums[right_ind][1][0]
            else:
                c_objs=nums[right_ind][1][get_states_ar_ind(nums,right_ind)]

            for i in range(c_objs_count):
                dst_row= c_objs[i]

                if dst_row >= c_counts[i]:
                    _cexit("invalid row",dst_row,nums[right_ind][1])

                dst_row = (rand_asg[right_ind][i])[dst_row]
                new_comb[i]=dst_row

            for i in range(wt_count):
                wt=within_trials[i]
                wt_id=wt_cells[i][0]

                params=[]
                for ind in wt_cells[i][1]:
                    params.append(new_comb[ind])

                ans=get_wt_val(asg_wt_vf[i],params)
                new_comb[wt_id]=ans

            for i in range(trans_count):
                target_cell=trans_cells[i][1]
                trans_ind=trans_cells[i][0]

                source_row=permut[loc][target_cell]
                dst_row=new_comb[target_cell]

                ans=(asg_vf[i])[source_row][dst_row]

                new_comb[trans_ind] = ans

            comb=comb_index(new_comb)
            cap=get_cap(new_comb)

            if nums[comb][0]<cap:
                nums[comb][0] += 1

                if unweighted_experiment:
                    clear_single_row(nums[comb][1][0])
                else:
                    clear_single_row(nums[comb][1][ get_states_ar_ind(nums,comb) ])

                loc+=1
                permut[loc]=new_comb

            else:
                #we increment nums at the beginning of the loop
                pass

'''
    Local function to print the result. Not used when the module
    is called by sweetpea core.
'''
def print_permut(pre,perm):
    m=[]

    for i in range(comb_len):
        line=[]
        for j in range(len(objects[i])):
            line.append(objects[i][j])
        m.append(line)

    s=""
    comb=""

    if trans_count>0:
        for i in range(c_objs_count+wt_count):
            comb+= "{} | ".format(m[i][pre[i]])
        s+=comb+"\n"

    for i in range(M):
        comb=""
        for j in range(c_objs_count):
            label=m[j][perm[i][j]]
            comb+= "{} | ".format(label)
        comb+=" - "

        for j in range(c_objs_count,comb_len):
            comb+= "{} | ".format(m[j][perm[i][j]])
        s+=comb+"\n"

    print(s)

'''
    An extra layer of validity check after each answer is formed.
    Not used when called by sweetpea core.
    This function checks validity of the cross, predicate values and weights.
'''
def check_result(pre,permut):
    if trans_count>0:
        for i in range(trans_count):
            trans_id=trans_cells[i][0]
            c=trans_cells[i][1]

            src=pre[c]
            dst=permut[0][c]

            ans=(asg_vf[i])[src][dst]

            if ans != permut[0][trans_id]:
                return False

        for i in range(wt_count):
            wt_id=wt_cells[i][0]

            params=[]
            for ind in wt_cells[i][1]:
                params.append(permut[0][ind])
            ans=get_wt_val(asg_wt_vf[i],params)

            if ans != permut[0][wt_id]:
                return False

    combs={}
    weighted_inds={}

    for i in range(M):
        comb=permut[i]

        index=comb_index(comb)
        if index not in combs:
            combs[index]=1
        else:
            combs[index]+=1

        weighted_inds[index]= get_cap(comb)

        for j in range(wt_count):
            wt_id=wt_cells[j][0]

            params=[]
            for ind in wt_cells[j][1]:
                params.append(comb[ind])
            ans=get_wt_val(asg_wt_vf[j],params)

            if ans != comb[wt_id]:
                return False



        if i==M-1:
            break

        next_comb=permut[i+1]
        for j in range(trans_count):
            trans_id=trans_cells[j][0]
            target_c=trans_cells[j][1]

            src=comb[target_c]
            dst=next_comb[target_c]

            ans=(asg_vf[j])[src][dst]

            if ans != next_comb[trans_id]:
                return False


    if len(combs) != M_raw:
        return False

    for ind in combs:
        if weighted_inds[ind] != combs[ind]:
            return False

    return True


'''
    Each permutation is created in the following order:
        primary objects
        within trials
        transitions

    If a within trial is dependent on a previous within trial,
    it must come after that    in the within_trials array.
    The user is expected not to pass a dependent factor before
    its arguments.

'''

# we expect an arg of a transition to be a non-transition
def transition_dependency_check():
    for t in transitions:
        if t[2]>= trans_cell_start:
            _cexit("Invalid transition:",t[0])


# No forward referencing
def wt_dependency_check():
    for i in range(len(within_trials)):
        w=within_trials[i]
        w_ind_perm = c_objs_count + i
        for arg in w[2]:
            if arg >=w_ind_perm:
                _cexit("Invalid derived constraint:",w[0])

def get_wt_val(ar,perm):
    cur=ar
    for i in range(0,len(perm)-1):
        cur=cur[perm[i]]
    return cur[perm[-1]]


def sigalrm_hand(sig,frame):
    _cexit("Experiment not solvable. Change your crossing or constraints.")


'''
    Itermediate classes for the objects that we need to parse in this module.
    These itermediary objects store only what we need to create our own encoding not
    the entire information in the original objects.
    SMGen does not recognize sweetpea classes. Any new class, object or structure
    from sweetpea core that is going to be used in SMGen must be first defined for
    the module.

'''
class _Factor:
    def __init__(self,name,initial_levels):
        self.name=name
        self.levels=initial_levels # initial_levels to match sweetpea naming convention
        '''
            cell_index is used to replace object arguments with the
            corresponding indices. Since transitions cannot be arguments to
            any factors, this member is not used for them but we set it anyways.
        '''


        self.cell_index=-1

        primary_types=[str,int,float]
        if type(self.levels[0]) in primary_types:
            self.type=0
        elif type(self.levels[0])==_DerivedLevel:
            self.type=self.levels[0].type
            self.args=self.levels[0].dr_level.args
            self.weighted=False

            for l in self.levels:
                if l.weight>1:
                    self.weighted=True
                    break
        else:
            _cexit("Unsupported factor:",name)

class _DerivedLevel:
    def __init__(self,name,l,weight=1):
        self.name=name
        self.dr_level=l
        self.weight=weight

        if type(l)==_WithinTrial:
            self.type=1
        elif type(l)==_Transition:
            self.type=2
        else:
            _cexit("Unsupported DerivedLevel")



class _WithinTrial:
    def __init__(self,func,args):
        self.func=func
        self.args=args

class _Transition:
    def __init__(self,func,args):
        self.func=func
        self.args=args
        #if len(args)!=1:
        #    print("[!] Unsupported transition")

class PrimaryObject:
    def __init__(self, name, levels, factor):
        self.name = name
        self.levels = levels
        self.factor = factor
        
'''
     We add the factor just as a reference. For example, to set a factor cell index.
     All object gourps will have the original Factor appended to the list.

     Primary object structure:
     [group name , levels , Factor obj reference]
'''
def add_primary(factor):
    levels=factor.levels
    primary_objects.append(PrimaryObject(factor.name, factor.levels, factor))

def add_wt(factor):
    levels=factor.levels
    args=factor.args
    levels_internal=[]
    w_ind=[]
    w_w=[]


    for l in levels:
        line= [l.name , l.dr_level.func, l.weight]
        levels_internal.append(line)
        if len(l.dr_level.args)!=len(args):
            _cexit("invald wt args")

        for i in range(len(args)):
            if args[i]!=l.dr_level.args[i]:
                _cexit("invalid wt args")

    within_trials.append([factor.name,levels_internal,args, factor])

def add_transition(factor):
    levels=factor.levels

    if len(factor.args)>1:
        _cexit("Unsupported Factor. Transition with multiple arguments:",factor.name)

    arg=factor.args[0] #single arg
    levels_internal=[]

    for l in levels:
        line= [l.name , l.dr_level.func, l.weight]
        levels_internal.append(line)
        if  l.dr_level.args[0] != arg :
            _cexit("invald tr arg")

    transitions.append([factor.name,levels_internal,arg, factor])


def define_cross(cross_f):
    global cross

    cross_inds=[]
    for f in cross_f:
        cross_inds.append(f.cell_index)

    cross=cross_inds

    return cross_inds


def print_factors():
    print("\n**************************************")
    print("Primary:")
    for o in primary_objects:
        print(o.name,o.levels,o.factor.cell_index,"Reference:",o[2])
    print("\n")

    print("WhithinTrials:")
    for o in within_trials:
        print(o[0],o[3].cell_index)
        for l in o[1]:
            print("\t{} {} {}".format(l[0],l[1],l[2]))
        print("\tArgs: {} ".format(o[2]))

    print("\n")

    print("Transitions:")
    for o in transitions:
        print(o[0],o[3].cell_index)
        for l in o[1]:
            print("\t{} {} {}".format(l[0],l[1],l[2]))
        print("\tArg: {}".format(o[2]))
    print("**************************************\n\n")

def encode_weights():
    for wt in within_trials:
        obj=wt[3]
        levels=wt[1]
        if obj.weighted:
            inds=[obj.cell_index]
            w=[]

            for i in range(len(levels)):
                l=levels[i]
                l_weight=l[2]
                if l_weight>1:
                    inds.append(i)
                    w.append(l[2])

            weighted_objects_init.append(inds)
            weights_init.append(w)

    for tr in transitions:
        obj=tr[3]
        levels=tr[1]
        if obj.weighted:
            inds=[obj.cell_index]
            w=[]
            for i in range(len(levels)):
                l=levels[i]
                if l[2]>1:
                    inds.append(i)
                    w.append(l[2])

            weighted_objects_init.append(inds)
            weights_init.append(w)

def encode_experiment(args):
    ind=0
    for factor in args:
        t=factor.type
        if t==0:
            add_primary(factor)
        elif t==1:
            add_wt(factor)
        elif t==2:
            add_transition(factor)

    ind=0
    for o in primary_objects:
        o.factor.cell_index=ind
        ind+=1
    for o in within_trials:
        o[3].cell_index=ind
        ind+=1
    for o in transitions:
        o[3].cell_index=ind
        ind+=1


    for o in within_trials:
        for i in range(len(o[2])):
            o[2][i] = o[2][i].cell_index

    for o in transitions:
        o[2] = o[2].cell_index

    encode_weights()

if __name__=="__main__":
    pass


def execute(answers_count=1, maximum_trials=False):
    global cross,wt_count,trans_count,c_objs_count,trans_cell_start,unweighted_experiment,asg_vf
    global asg_wt_vf,combs_weights,M,M_raw,L,comb_len,trans_in_crossing

    if len(cross)<1:
        _cexit("Invalid input.")

    '''
        Get cross members weights.
        weighted_objects and weights must match cross. No extra members in them.
    '''
    if len(weighted_objects_init)>0:
        for i in range(len(weighted_objects_init)):
            obj=weighted_objects_init[i]
            if obj[0] in cross: #linear search. init operation
                weighted_objects.append(obj)
                weights.append(weights_init[i])

    tmp_dc={}
    for e in cross:
        tmp_dc[e]=1

    if len(tmp_dc) != len(cross):
        _cexit("Invalid cross. Check your input.")


    wt_count = len(within_trials)

    '''
        Init all structures and build transition maps:
    '''

    trans_count=len(transitions)

    for o in primary_objects:
        c_counts.append(len(o.levels))
    c_objs_count = len(c_counts)    # number of main object groups

    trans_cell_start=c_objs_count+wt_count

    trans_in_crossing=False
    for e in cross:
        if e >= trans_cell_start:
            trans_in_crossing=True

    transition_dependency_check()
    wt_dependency_check()

    for i in range(c_objs_count):
        line=[]
        for j in range(len(primary_objects[i].levels)):
            obj=str(primary_objects[i].name) + " " + str(primary_objects[i].levels[j])
            line.append(obj)
        objects.append(line)

    for i in range(wt_count):
        line=[]
        for j in range(len(within_trials[i][1])):
            obj=within_trials[i][0] + " " + within_trials[i][1][j][0]
            line.append(obj)
        objects.append(line)

    for i in range(trans_count):
        line=[]
        for j in range(len(transitions[i][1])):
            obj=transitions[i][0] + " " + transitions[i][1][j][0]
            line.append(obj)
        objects.append(line)


    for o in objects:
        obs_counts.append(len(o))

    comb_len = len(obs_counts)

    if len(weighted_objects)==0 :
        unweighted_experiment = True
    else:
        unweighted_experiment= False

    if not unweighted_experiment:
        if len(weighted_objects) != len(weights):
            _cexit("Invalid user input")

        w_dc={}
        for i in range(len(weighted_objects)):
            ind=weighted_objects[i][0]
            w_dc[ind]=[weighted_objects[i][1:], weights[i]]

        for i in range(len(objects)):
            line=[1]*len(objects[i])
            if i not in w_dc:
                all_weights.append(line)
            else:
                for j in range(len(w_dc[i][0])):
                    ind=(w_dc[i][0])[j]
                    line[ind]=(w_dc[i][1])[j]
                all_weights.append(line)

        for i in range(len(cross)):
            cross_weights.append(all_weights[cross[i]])

    for ind in cross:
        cross_counts.append(len(objects[ind]))

    M = perms_count(0)
    M_raw = perms_count(1)
    L=M

    asg_tmp=[]
    for i in range(trans_count):
        target_c = transitions[i][2]
        trans_cells.append([trans_cell_start+i,target_c])

        if target_c < c_objs_count:
            c_levels=primary_objects[target_c].levels
            c_count=c_counts[target_c]
        else:
            c_levels=[]
            for z in range(len(within_trials[target_c-c_objs_count][1])):
                c_levels.append(within_trials[target_c-c_objs_count][1][z][0]) # use string name as the level value
            c_count=len(c_levels)

        funcs = []
        for lev in transitions[i][1]:
            funcs.append(lev[1])

        asg_vf_i=[]

        for j in range(c_count):
            f_line=[]
            for z in range(c_count):
                f_line.append(-1)
            asg_vf_i.append(f_line)

        for j in range(c_count):
            for z in range(c_count):
                src=c_levels[j]
                dst=c_levels[z]

                answers=[]
                for f_ind in range(len(funcs)):
                    arg=[-1,-1]
                    arg[0]=dst
                    arg[-1]=src

                    ans=funcs[f_ind](arg)
                    if ans==True:
                        answers.append(f_ind)
                if len(answers)!=1:
                    _cexit("Invalid predicate functions for transition:",transitions[i][0])

                asg_vf_i[j][z]=answers[0]

        asg_tmp.append(asg_vf_i)

    asg_vf = asg_tmp

    def get_wt_ans(perm,funcs):
        answers=[]
        for i in range(len(funcs)):
            f=funcs[i]
            ans=f(*perm)
            if ans==True:
                answers.append(i)
        if len(answers)!=1:
            _cexit("Invalid WithinTrial transition.")
        return answers[0]

    def put_wt_val(ar,perm,ans):
        cur=ar

        for i in range(0,len(perm)-1):
            cur=cur[perm[i]]

        cur.append(ans)

    def wt_append_new(ar,perm,until):
        cur=ar
        for i in range(0,until):

            cur=cur[perm[i]]

        empty=[]
        level=empty
        for i in range(until+1,len(perm)-1):
            level.append([])
            level=level[0]

        cur.append(empty)

    def perm_to_levels(levels,perm):
        r=[]
        for i in range(len(perm)):
            ind=perm[i]
            r.append(levels[i][ind])

        return r

    asg_tmp=[]
    for i in range(wt_count):
        target_cells = within_trials[i][2]
        wt_cells.append([c_objs_count+i,target_cells])

        funcs = []
        for lev in within_trials[i][1]:
            funcs.append(lev[1])


        perm=[0]*len(target_cells)
        counts=[-1]*len(target_cells)
        levels=[]

        for j in range(len(target_cells)):
            cell=target_cells[j]
            if cell < c_objs_count:
                #primary object
                counts[j]=len(primary_objects[cell].levels)
                levels.append(primary_objects[cell].levels)
            else:
                #within trial (unlikely to happen)
                counts[j]=len(within_trials[cell-c_objs_count][1])
                l=[]
                for z in range(len(within_trials[cell-c_objs_count][1])):
                    l.append(within_trials[cell-c_objs_count][1][z][0])

                levels.append(l)


        asg_vf_i=[]
        cur=asg_vf_i
        for j in range(len(target_cells)-1):
            cur.append([])
            cur=cur[0]


        last=len(target_cells)-1
        loc=0

        while 1:

            vals=perm_to_levels(levels,perm)
            ans=get_wt_ans(vals,funcs)
            put_wt_val(asg_vf_i,perm,ans)

            if perm[last] == counts[last]-1:
                if last==0:
                    break

                perm[last]=0
                finished=0
                for j in range(last-1,-1,-1):
                    if perm[j]==counts[j]-1:
                        if j==0:
                            finished=1
                            break
                        else:

                            perm[j]=0
                            continue

                    wt_append_new(asg_vf_i,perm,j)
                    perm[j] += 1
                    break
                if finished:
                    break
            else:
                perm[last]+=1
        asg_tmp.append(asg_vf_i)

    asg_wt_vf=asg_tmp


    combs_weights=[-1]*M_raw
    loc=0
    perm=[0]*comb_len
    last=comb_len-1
    while 1:
        ind=comb_index(perm)
        combs_weights[ind]=get_cap(perm)

        if perm[last] == obs_counts[last]-1:
            if last==0:
                break

            perm[last]=0
            finished=0
            for j in range(last-1,-1,-1):
                if perm[j]==obs_counts[j]-1:
                    if j==0:
                        finished=1
                        break
                    else:

                        perm[j]=0
                        continue

                perm[j] += 1
                break
            if finished:
                break
        else:
            perm[last]+=1

    iterations=answers_count # number of requested answers

    # signal(SIGALRM,sigalrm_hand)

    timer = threading.Timer(EXEC_TH, sigalrm_hand)
    timer.start()

    # setitimer(ITIMER_REAL,EXEC_TH,0)


    def add_answer(pre,r,answers,maximum_trials):
        a={}

        for i in range(c_objs_count):
            key=primary_objects[i].name
            vals=[]

            if trans_in_crossing:
                v=pre[i]
                v=primary_objects[i].levels[v]
                vals.append(v)

            for p in r:
                v=p[i]
                v=primary_objects[i].levels[v]
                vals.append(v)
            if maximum_trials:
                vals = vals[0:maximum_trials]
            a[key]=vals


        for i in range(wt_count):
            key=within_trials[i][0]
            vals=[]

            c_ind=i+c_objs_count
            if trans_in_crossing:
                v=pre[c_ind]
                v=within_trials[i][1][v][0]

                vals.append(v)

            for p in r:
                v=p[c_ind]
                v=within_trials[i][1][v][0]
                vals.append(v)
            if maximum_trials:
                vals = vals[0:maximum_trials]
            a[key]=vals

        for i in range(trans_count):
            key=transitions[i][0]
            vals=[]

            c_ind=i+c_objs_count+wt_count
            if trans_in_crossing:
                vals.append('')

            for p in r:
                v=p[c_ind]
                v=transitions[i][1][v][0]
                vals.append(v)
            if maximum_trials:
                vals = vals[0:maximum_trials]
            a[key]=vals

        answers.append(a)

    exp_answers=[]

    for i in range(iterations):
        time_s=(time())

        pre,r=sm_backtrack_random()

        time_s=(time()) - time_s

        # print("Experiment {} completed...".format(i))
        #print_permut(pre,r)

        add_answer(pre,r,exp_answers,maximum_trials)

        if time_s<1:
            fmt="{:.4f}"
        else:
            fmt="{:d}"
            time_s=int(time_s)


        '''
        print("[>] Operation completed in "+(fmt+" secs.").format(time_s))

        v=check_result(pre,r)

        if v:
            v="\033[1;92mVALID\033[0m"
        else:
            v="\033[31mINVALID\033[0m"
        print("Post generation validity check: {}\n".format(v))
        '''
        timer.cancel()
        # timer = threading.Timer(0)#, on_timer)
        # timer.start()
        # setitimer(ITIMER_REAL,0,0) #disable timer

    return exp_answers
