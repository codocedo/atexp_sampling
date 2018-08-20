# TEST FROM SCRATCH
import sys
import time
from itertools import combinations

from lib.enumerations import LectiveEnum
from lib.representations import PairSet, Partition, Expert


SPLIT = 0.0001
G = set([])



def read_csv(path, separator=','):
    mat = [map(str, line.replace('\n','').split(separator)) for line in open(path, 'r').readlines()]
    return [[row[j] for row in mat] for j in range(len(mat[0]))]


def l_close(pat, L):
    #print L
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

    
def execute():
    '''
    Execute the FD MINER extraction process based on PSEUDO CLOSURES
    building a minimal basis of FDs
    '''
    file_input_path = sys.argv[1]
    
    # READ DATABASE
    db = Expert(split=SPLIT)
    db.read_csv(file_input_path)

    L = [] # FD DATABASE

    # Enumeration of candidates
    enum = LectiveEnum(len(db.atts)-1)

    # First candidate
    intent = []
    enum.next(intent)
    iterations = 0

    class Top(object):
        @staticmethod
        def intersection(other):
            return other

    # Stack keeps the record for the next enumerations
    stack = [([],Top())]

    t0 = time.time()

    
    while intent != [-1]:

        for prevint, prevext in reversed(stack):
            if len(intent) < len(prevint) or any(x not in intent for x in prevint):
                stack.pop()
            else:
                break

        iterations+=1
        
        print '\r {:<30}'.format(intent),
        # print stack
        sys.stdout.flush()

        preintent = l_close(intent, L)
        s_preintent = sorted(preintent)
        
        if any(i>j for i,j in zip(intent, s_preintent)):
            enum.next(enum.last(intent))
            continue

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

        prevint, prevext = stack[-1]
        
        # preextent = reduce(lambda x, y: x.intersection(y), [db.ps[i] for i in preintent])
        # print stack[-3:]
        # print intent, prevint
        new_att = [i for i in intent if i not in prevint][0]
        # print "NEWATT", new_att
        preextent = prevext.intersection(db.ps[new_att])# reduce(lambda x, y: x.intersection(y), [db.ps[i] for i in preintent])
        
        # print db.ps.items()
        closed_preintent = set([i for i, j in db.ps.items() if i not in preintent and preextent.leq(j)])
        # closed_preintent = set([i for i, j in db.ps.items() if i not in preintent and pat_leq(preextent, j)])
        go_on = bool(closed_preintent)
    
        while go_on:
            # print '\t::', preintent
            AJJ = closed_preintent.union(preintent)
            AII, AI = db.check(preintent, preextent)
            # print '\n',AII, AJJ, '::',closed_preintent, AII==AJJ

            if AII == AJJ:

                L.append((preintent, closed_preintent.union(preintent)))
                
                if max(intent) < min(closed_preintent):
                    # print 'y'
                    intent = sorted(closed_preintent.union(preintent))
                else:
                    # intent = sorted(preintent)
                    # print 'x'
                    enum.last(intent)
                go_on=False
                # exit()
                break
            else:
                # print AII, AJJ
                db.increment_sample(AI, AJJ)
                # exit()
            # print preextent, preintent, [db.ps[i] for i in preintent]
            preextent = reduce(lambda x, y: x.intersection(y), [db.ps[i] for i in preintent])
            # print preextent
            # exit()
            closed_preintent = set([i for i, j in db.ps.items() if i not in preintent and preextent.leq(j)])
            go_on = bool(closed_preintent)
        if len(intent) < len(preintent) and any(i < new_att for i in preintent):
            # print '????'
            intent = sorted(preintent)
        # print '==>',new_att, intent, preintent, closed_preintent
        stack.append((preintent, preextent))
        # else:
        # intent = sorted(preintent)
        
        enum.next(intent)
    print
    # print L
    print len(L)
    print iterations 
    print "SAMPLE", len(list(db.sample)), "REAL", len(G), "INCREMENTS:", db.increments
    print 'Time:', time.time()-t0
    # for ri, (i, j) in enumerate(L):
    #     print ri+1, i, j-i
    print 
    #print cache

if __name__ == "__main__":
    execute()