# TEST FROM SCRATCH
import sys
import time
from itertools import combinations

from lib.enumerations import LectiveEnum
from lib.representations import PairSet, Partition, Expert


SPLIT = 0
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
        @staticmethod
        def add(obj):
            pass

    # Stack keeps the record for the next enumerations
    stack = [([],Top(), Top())]

    t0 = time.time()

    
    while intent != [-1]:
        # print "\nSTACK",[(i[0], i[2]) for i in stack]
        preintent = l_close(intent, L)


        s_preintent = sorted(preintent)

        print '\r >>>{:<30}'.format(intent),
        # print stack
        sys.stdout.flush()

        
        
        if any(i>j for i,j in zip(intent, s_preintent)):
            enum.next(enum.last(intent))
            continue
            
        for prevint, prevext, prevAI in reversed(stack):
            if len(preintent) < len(prevint) or any(x not in preintent for x in prevint):
                stack.pop()
                # print 'pop'
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
        
        # preextent = reduce(lambda x, y: x.intersection(y), [db.ps[i] for i in preintent])
        # print stack[-3:]
        # print intent, prevint
        new_att = [i for i in intent if i not in prevint][-1]
        # print "NEWATT", new_att
        # preextent = # 
        preextent = prevext.intersection(db.ps[new_att])

        closed_preintent = set([i for i, j in db.ps.items() if i not in preintent and preextent.leq(j)])
        # closed_preintent = set([i for i, j in db.ps.items() if i not in preintent and pat_leq(preextent, j)])
        go_on = bool(closed_preintent)
        AI = None
        # print '\t', closed_preintent
        while go_on:
            # AJJ = closed_preintent.union(preintent)
            AII, AI = db.check(new_att, prevint, closed_preintent, prevAI)
            # print AII, closed_preintent
            if AII == closed_preintent:
                # print ':)'

                L.append((preintent, closed_preintent.union(preintent)))
                
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
                closed_preintent = set([i for i in closed_preintent if preextent.leq(db.ps[i])])

            go_on = bool(closed_preintent)

        if len(intent) < len(preintent) and any(i < new_att for i in preintent):
            intent = sorted(preintent)
        # print "adding", preintent
        stack.append((preintent, preextent, AI))
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