import argparse
import random
from itertools import combinations
from ae_libs import read_csv, match
from ae_libs.fd_tree import FDTree
import sys


class Partition(object):
    '''
    Partiton representation, split partitions
    list of sets
    '''
    N_TUPLES = 0
    TOP = None
    @staticmethod
    def top():
        if Partition.TOP is None:
            # Partition.TOP = [set(range(Partition.N_TUPLES))]
            Partition.TOP = [set(range(Partition.N_TUPLES))]
        return Partition.TOP

    @staticmethod
    def nparts(desc):
        return len(desc) + Partition.N_TUPLES - (sum([len(i) for i in desc]))

    @staticmethod
    def from_lst(lst):
        Partition.N_TUPLES = max(len(lst), Partition.N_TUPLES)
        hashes = {}
        for i, j in enumerate(lst):
            hashes.setdefault(j, set([])).add(i)

        return Partition.fix_desc(hashes.values())

    @staticmethod
    def fix_desc(desc):
        desc = [i for i in desc if len(i) > 1]
        desc.sort(key=lambda k: (len(k), min(k)), reverse=True)
        if len(desc) == 0:
            desc.append(set([]))
        return desc
    @staticmethod
    def intersection(desc, other):
        '''
        Procedure STRIPPED_PRODUCT defined in [1]
        '''
        # print desc, other
        new_desc = []
        T = {}
        S = {}
        for i, k in enumerate(desc):
            for t in k:
                T[t] = i
            S[i] = set([])
        
        for i, k in enumerate(other):
            for t in k:
                if T.get(t, None) is not None:
                    S[T[t]].add(t)
            for t in k:
                if T.get(t, None) is not None:
                    if len(S[T[t]]) > 1:
                        new_desc.append(S[T[t]])
                    S[T[t]] = set([])
        return Partition.fix_desc(
            new_desc
        )


    @staticmethod
    def leq(desc, other, cache):
        '''
        Procedure STRIPPED_PRODUCT defined in [1]
        '''
        if len(desc) == 1 and len(desc[0]) == 0:
            return True
        # if other.nparts > self.nparts:
        #     return False
        T = {}

        for i, k in enumerate(other):
            for t in k:
                T[t] = i
        
        for i, k in enumerate(desc):
            
            it = iter(k)
            ti = next(it)
            

            mvalue = T.get(ti, -1)
            fpair = [ti]
            for ti in it:
                if T.get(ti, -2) != mvalue:
                    fpair.append(ti)
                    # cache[tuple(fpair)] = match(fpair[0], fpair[1])
                    
                    return False
        return True

class PreClosure(object):
    def __init__(self, L, n_atts):
        self.L = L
        self.n_atts = n_atts

    def l_close(self, pat):
        # print 'LCLOSE', pat, self.L
        newpat = set(pat)
        
        complement = set([])
        while True:
            if len(newpat) == self.n_atts:
                break
            subparts = [con for ant, con in self.L if ant.issubset(newpat)]
            if bool(subparts):
                complement = reduce(set.union, subparts)
                if complement.issubset(newpat):
                    break
                else:
                    newpat.update(complement)
            else:
                break
        return newpat


def examples(n_tuples):
    random_order = range(n_tuples)
    random.shuffle(random_order)
    for t1, t2 in combinations(random_order, 2):
        yield (t1, t2)


class Oracle(object):
    def __init__(self, n_tuples, U, ps):
        self.n_tuples = n_tuples
        self.U = U
        self.ps = ps

    def close(self, C):
        # print '**'
        # print "{}??".format(C)
        if bool(C):
            new_ps = reduce(Partition.intersection, [self.ps[x] for x in C])
        else:
            new_ps = [set(range(self.n_tuples))]
        cache = {}
        new_C = [x for x in self.U if x not in C and Partition.leq(new_ps, self.ps[x], cache)]
        # print '\t=',new_C
        # print '**'
        return C.union(new_C)

    def is_not_actual_model(self, C):
        # print '**'
        # print "{}??".format(C)
        if bool(C):
            new_ps = reduce(Partition.intersection, [self.ps[x] for x in C])
        else:
            new_ps = [set(range(self.n_tuples))]
        cache = {}
        new_C = [x for x in self.U if x not in C and Partition.leq(new_ps, self.ps[x], cache)]
        # print '\t=',new_C
        # print '**'
        return bool(new_C)

from itertools import combinations
def exec_alg33(tuples):
    
    

    U = range(len(tuples[0])) # Attributes
    representations = [[row[j] for row in tuples] for j in U]
    partitions = map(Partition.from_lst, representations)

    oracle = Oracle(len(tuples), U, partitions)

    potU = []
    for i in range(1,len(U)):
        for x in combinations(U, i):
            potU.append(set(x))
    
    
    m_prime = [set([]) for i in range(len(U))]

    L = []
    pc = PreClosure(L, len(U))

    n_tuples = len(tuples)
    print len(potU)
    cycles = 0
    while True:
        X = None
        for lhs, rhs in L:
            if oracle.is_not_actual_model(rhs):
                X = set(rhs)
                break
        if X is None:
            X = set(random.choice(potU))
        cycles+=1
        sys.stdout.flush()
        # print oracle.is_not_actual_model(X)
        cond1 = pc.l_close(X) == X
        cond2 = oracle.is_not_actual_model(X)
        print '\r', cycles, len(L), cond1, cond2,X,  
        if cond1 and cond2:
            # print '-', X, L
            found = False
            for ri, (A, B) in enumerate(L):
                C = A.intersection(X)
                if C != A and oracle.is_not_actual_model(C):
                    L[ri][0].intersection_update(X)
                    found = True
                    break
            if not found:
                L.append((X, set(U)))
            # print '\t', L
        elif not cond1 and not cond2:
            # print '+', X, L
            for ri, (A, B) in enumerate(L):
                if A.issubset(X) and not B.issubset(X):
                    L[ri][1].intersection_update(X)
            # print '\t', L
        else:
            continue
        for ri in range(len(L)-1, -1, -1):
            if L[ri][0] == L[ri][1]:
                del L[ri]
    



if __name__ == '__main__':
    __parser__ = argparse.ArgumentParser(description='FD Miner - Sampling-based Version')
    __parser__.add_argument('database', metavar='database_path', type=str, help='path to the formal database')
    __parser__.add_argument('-s', '--separator', metavar='separator', type=str, help='Cell separator in each row', default=',')
    args = __parser__.parse_args()
    tuples = read_csv(args.database, separator=args.separator)
    exec_alg33(tuples)