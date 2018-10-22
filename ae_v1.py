# TEST FROM SCRATCH
import sys
import time
import json
import argparse
import logging

from itertools import combinations

from ae_libs.enumerations import LectiveEnum
from ae_libs.representations import PairSet, Partition, Expert, Top, ExpertLinearSampler, ExpertPartitionSampler
from ae_libs.fd_tree import FDTree, FDList, FDOList


from math import factorial as fac

def binomial(x, y):
    try:
        binom = fac(x) // fac(y) // fac(x - y)
    except ValueError:
        binom = 0
    return binom

FORMAT = "[%(filename)s:%(lineno)s - %(funcName)20s() ] %(message)s"

logging.basicConfig(format=FORMAT, level=logging.INFO)
logger = logging.getLogger(__name__)


def execute(**params):
    '''
    Execute the FD MINER extraction process based on PSEUDO CLOSURES
    building a minimal basis of FDs
    '''
    # CONFIGURE
    file_input_path = params['database']
    
    # Stack keeps the record for the next enumerations
    stack = [[[], Top(), Top()]]

    # READ DATABASE
    DBClass = ExpertLinearSampler
    if params.get("use_patterns", False):
        DBClass = ExpertPartitionSampler

    db = DBClass(
        stack=stack
    )
    db.read_csv(file_input_path, separator=params.get("separator", ','), has_headers=params.get("ignore_headers", False))
    
    # Stores the FDs found throught the execution
    fd_store = FDList(db.n_atts) # FD DATABASE

    # Adds the first FD []->M, necessary for some databases
    rhs = set(db.get_top_atts())
    if bool(rhs):
        fd_store.add(set([]), rhs)

    # Creates the enumerator of candidates
    enum = LectiveEnum(len(db.atts)-1)

    # Creates the first candidate
    intent = []
    enum.next(intent)

    # Counters
    iterations = 0
    shorts = 0
    shorts2 = 0
    shorts3 = 0
    wit = 0
    t0 = time.time()

    
    print '({:<5}|{:<5}|{:<5}|{:<5}|{:<5}|{:<5}|{:<5}) {:<40}'.format("FDs", "SAMP", "QUERY", "IT","NFDs", "SHORT",  "MNFD", "CURRENT_INTENT")
    while intent != [-1]:
        
        preintent = fd_store.l_close(intent)

        s_preintent = sorted(preintent)
        
        print '\r({:<5}|{:<5}|{:<5}|{:<5}|{:<5}|{:<5}|{:<5}) {:<60}'.format(fd_store.n_fds, len(db.sample), shorts2, iterations,db.non_fds.n_elements, shorts, shorts3, intent[-20:]),
        sys.stdout.flush()
        
        '''
        Consider that L[12, 14] = [1, 12, 14]
        In this case we ignore the intent and proceed to [12, 13]
        '''
        if any(i>j for i,j in zip(intent, s_preintent)):
            enum.next(enum.last(intent))
            continue
        

        # CHECK AND UPDATE THE STACK
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
        
        # logger.debug([i for i in fd_store.read_fds()])
        logger.debug("Previous Intent:{}|Current Intent:{}".format(prevint, intent)),
        
        new_att = [i for i in intent if i not in prevint][-1]
        
        preextent = prevext.intersection(db.ps[new_att])
        
        match = [i in preintent for i in range(db.n_atts)]

        AI = None

        go_on = match not in db.non_fds
        shorts3 += not go_on

        checked = False
        new_fd = False
        while go_on:
            wit+=1
            closed_preintent = set([i for i, j in db.ps.items() if i not in preintent and preextent.leq(j)])
            logger.debug("Intent:{}|PreIntent:{}|Closed Preintent:{}".format(intent, preintent, closed_preintent))

            if not bool(closed_preintent):
                shorts+=not checked
                # for i in closed_preintent:
                #     match[i] = True
                # print match
                break

            if not checked:
                print '[',
                sys.stdout.flush()
                AII, AI = db.check(new_att, prevint, closed_preintent, prevAI, preintent)
                print ']',
                sys.stdout.flush()
                checked = True
                shorts2 += 1

            if AII == closed_preintent:
                new_fd = True
                # print '\t', preintent, '=>', closed_preintent
                fd_store.add(preintent, closed_preintent)#.union(preintent)-preintent)
                
                if max(intent) < min(closed_preintent):
                    intent = sorted(closed_preintent.union(preintent))
                else:
                    enum.last(intent)
                break

            else:
                print '<',
                sys.stdout.flush()
                new_obj = db.increment_sample(AI, AII, closed_preintent, preintent, preextent)
                print '>',
                sys.stdout.flush()
                
                preextent.update(new_obj)

                for i, j, k in stack:
                    j.update(new_obj)                

        if not new_fd:
            intent = s_preintent

        stack.append([preintent, preextent, AI])
        enum.next(intent)

    print

    print "N_FDS:", fd_store.n_fds
    print "ITERATIONS:", iterations 
    print "SAMPLE", len(list(db.sample)), "INCREMENTS:", db.increments
    print 'Time:', time.time()-t0
    print "SHORTS:", shorts
    print "QUESTIONS_ASKED:", shorts2
    print "NOT FDS:", shorts3
    print "WHILES:", wit
    
    out = []
    for ri, (lhs, rhs) in enumerate(fd_store.read_fds()):
         out.append([sorted([db.partitions[i].idx for i in lhs]), sorted([db.partitions[i].idx for i in rhs if i not in lhs])])
    out.sort(key=lambda k: (len(k[0]), len(k[1]), tuple(k[0]), tuple(k[1])))
    with open(file_input_path+'.ae.out.json', 'w') as fout:
        json.dump(out, fout)


if __name__ == "__main__":
    __parser__ = argparse.ArgumentParser(description='FD Miner - Sampling-based Version')
    __parser__.add_argument('database', metavar='database_path', type=str, help='path to the formal database')
    __parser__.add_argument('-s', '--separator', metavar='separator', type=str, help='Cell separator in each row', default=',')
    __parser__.add_argument('-p', '--use_patterns', help='Use Pattern Structures for DB', action='store_true')
    __parser__.add_argument('-i', '--ignore_headers', help='Ignore Headers', action='store_true')
    args = __parser__.parse_args()
    
    execute(**vars(args))