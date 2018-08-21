# TEST FROM SCRATCH
import sys
import time
import json
from itertools import combinations

from ae_libs.enumerations import LectiveEnum
from ae_libs.representations import PairSet, Partition, Expert, Top, ExpertSampler
from ae_libs.fd_tree import FDTree


SPLIT = 0

def read_csv(path, separator=','):
    mat = [map(str, line.replace('\n','').split(separator)) for line in open(path, 'r').readlines()]
    return [[row[j] for row in mat] for j in range(len(mat[0]))]


def l_close(pat, L):
    newpat = set(pat)
    
    complement = set([])
    while True:
        subparts = [con for ant, con in L if len(ant) < len(newpat) and ant.issubset(newpat)]
        if bool(subparts):
            complement = reduce(set.union, subparts)
            if complement.issubset(newpat):
                break
            else:
                newpat.update(complement)
        else:
            break
    return newpat

def l2_close(pat, fd_store):
    newpat = set(pat)
    # fds = list(fd_store.read_fds())
    
    # print "FIND FOR ", pat
    
    while True:
        complement = reduce(set.union, [set([])]+[rhs for rhs in fd_store.find_rhss(newpat)])
        if complement.issubset(newpat):
            break
        newpat.update(complement)
    return newpat
            
    #     exit()

    
def execute():
    '''
    Execute the FD MINER extraction process based on PSEUDO CLOSURES
    building a minimal basis of FDs
    '''
    file_input_path = sys.argv[1]
    
    # Stack keeps the record for the next enumerations
    stack = [([], Top(), Top())]

    # READ DATABASE
    db = ExpertSampler(
        stack=stack,
        split=SPLIT
    )
    db.read_csv(file_input_path)

    L = [] # FD DATABASE
    fd_store = FDTree(db.n_atts)

    rhs = set(db.get_top_atts())
    if bool(rhs):
        L = [(set([]), rhs)]
        for r in rhs:
            fd_store.add(set([]), r)
    
    # Enumeration of candidates
    enum = LectiveEnum(len(db.atts)-1)

    # First candidate
    intent = []
    enum.next(intent)
    iterations = 0

    t0 = time.time()

    shorts = 0
    shorts2 = 0
    while intent != [-1]:
        # print "\nSTACK",[i[0] for i in stack]
        # preintent = l_close(intent, L)
        preintent = l2_close(intent, fd_store)
        
        
        s_preintent = sorted(preintent)
        
        # shorts2 += [i in intent for i in range(db.n_atts)] in db.non_fds

        print '\r {:<30}'.format(intent[-20:]),
        # print stack
        sys.stdout.flush()
        
        if any(i>j for i,j in zip(intent, s_preintent)):
            enum.next(enum.last(intent))
            continue
            
        for prevint, prevext, prevAI in reversed(stack):
            if len(preintent) < len(prevint) or any(x not in preintent for x in prevint):
                stack.pop()
            else:
                break
        
        iterations+=1

        # WE NEED TO RECOVER THE PREVIOUS EXTENT CALCULATED FOR THE PREFIX 
        # OF INTENT, RECALL THAT intent IS A PREFIX PLUS SOMETHING, AND WE
        # HAVE ALREADY CALCULATED THE EXTENT FOR THE PREFIX. HOWEVER, IT MAY
        # BE THAT AT SOME JUMP LIKE THE PREVIOUS ONE FOR THE PRE-INTENT OR THE 
        # FOLLOWING FOR THE CLOSED SETS, THE INTENT IS A PREFIX, PLUS A SET OF 
        # ATTRIBUTES. THUS, WE FIRSTLY NEED TO KNOW WHAT WAS THE PREVIOUS PREINTENT
        # IN THE THREE FOR WHICH WE CALCULATED AN EXTENT.

        # WE NEED TO CALCULATE THE PRE-EXTENT FOR THE PRE-INTENT
        # THE PREINTENT IS COMPOSED BY AN ENUMERATED INTENT AND A SET OF ATTRIBUTES
        # OBTAINED FROM THE PRECLOSURE.
        # TE INTENT ENUMERATED IS COMPOSED BY A PREFIX AND A

        prevint, prevext, prevAI = stack[-1]
        
        new_att = [i for i in intent if i not in prevint][-1]
        
        preextent = prevext.intersection(db.ps[new_att])
        AI = Partition([])

        match = [i in preintent for i in range(db.n_atts)]
        
        go_on = match not in db.non_fds
        shorts += match in db.non_fds

        while go_on:
            closed_preintent = set([i for i, j in db.ps.items() if i not in preintent and preextent.leq(j)])
            if not bool(closed_preintent):
                break
            # AJJ = closed_preintent.union(preintent)
            # print prevAI
            AII, AI = db.check(new_att, prevint, closed_preintent, prevAI)
            # print prevAI
            # print ''
            # print AII, closed_preintent
            if AII == closed_preintent:
                # print ':)'

                # L.append((preintent, closed_preintent.union(preintent)))
                fd_store.add(preintent, closed_preintent.union(preintent)-preintent)
                    
                
                if max(intent) < min(closed_preintent):
                    intent = sorted(closed_preintent.union(preintent))
                else:
                    enum.last(intent)
                go_on=False
                break

            else:

                new_obj = db.increment_sample(AI, AII, closed_preintent, preintent)

                preextent.add(new_obj)
                for i, j, k in stack:
                    j.add(new_obj)                


        if len(intent) < len(preintent) and any(i < new_att for i in preintent):
            intent = sorted(preintent)
        # print "adding", preintent
        stack.append((preintent, preextent, AI))
        enum.next(intent)

    print
    # print L
    print len(L)
    print iterations 
    print "SAMPLE", len(list(db.sample)), "INCREMENTS:", db.increments
    print 'Time:', time.time()-t0
    print "SHORTS:", shorts
    print "SHORTS2:", shorts2
    fds = list(fd_store.read_fds())
    print len(fds)
    # fd_store.print_tree()
    # for i in fds:
    #     print i

    out = []
    for ri, (lhs, rhs) in enumerate(L):
         out.append([sorted([db.partitions[i].idx for i in lhs]), sorted([db.partitions[i].idx for i in rhs if i not in lhs])])
    out.sort(key=lambda k: (len(k[0]), len(k[1]), tuple(k[0]), tuple(k[1])))
    with open(file_input_path+'.ae.out.json', 'w') as fout:
        json.dump(out, fout)
    #print cache

if __name__ == "__main__":
    execute()