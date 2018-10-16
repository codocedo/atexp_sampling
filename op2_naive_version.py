## OPTIMIZATION 1NAIVE VERSION
# USES STRIPED PARTITIONS

import csv
import sys
import copy
from ae_libs.enumerations import LectiveEnum
# from ae_libs.representations import Partition
from itertools import product

class Partition(object):
    '''
    Partiton representation, split partitions
    list of sets
    '''
    N_TUPLES = 0
    def __init__(self, desc):
        '''
        Sort and split the partition
        '''
        self.idx = None
        desc = [i for i in desc if len(i) > 1]
        desc.sort(key=lambda k: (len(k), min(k)), reverse=True)
        if len(desc) == 0:
            desc.append(set([]))
        super(Partition, self).__init__(desc)
        self._nparts = None

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
    def leq(desc, other):
        '''
        Procedure STRIPPED_PRODUCT defined in [1]
        '''
        for i in desc:
            if not any(i.issubset(j) for j in other):
                return False
        return True
#####

def leq_partitions(d1, d2):
    for pi in d1:
        if not any(pi.issubset(pj) for pj in d2):
            return False
    return True

def intersect_partitions(d1, d2):
    out = []
    for pi in d1:
        for pj in d2:
            pk = pi.intersection(pj)
            if bool(pk):
                out.append(pk)
    return out

def square(X, partitions):
    if bool(X):
        return reduce(Partition.intersection, [partitions[x] for x in X])
    else:
        return [set(range(Partition.N_TUPLES))]#[reduce(set.union, partitions[0])]

def square_closure(X, partitions):
    pattern = square(X, partitions)
    return set([i for i, p in enumerate(partitions) if Partition.leq(pattern, p)])

def make_partition_from_list(lst):
    hashes = {}
    for i, j in enumerate(lst):
        hashes.setdefault(j, set([])).add(i)
    return map(set, hashes.values())

def read_csv(path, separator=',', has_headers=False, quotechar='"'):
    '''
    Read csv into self._data
    self._data contains the original parsed file
    '''
    data = []
    with open(path, 'r') as csvfile:
        reader = csv.reader(csvfile, delimiter=separator, quotechar=quotechar)
        for line in reader:
            data.append(map(str, line))
    return data

def closed_set(X, g_prime, m_prime):
    if bool(X):
        extent = reduce(set.intersection, [m_prime[x] for x in X])
    else:
        extent = set(range(len(g_prime)))
    if bool(extent):
        intent = reduce(set.intersection, [g_prime[t] for t in extent])
    else:
        intent = set(range(len(m_prime)))
    return intent

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
            subparts = [con for ant, con in self.L if len(ant) < len(newpat) and ant.issubset(newpat)]
            if bool(subparts):
                complement = reduce(set.union, subparts)
                if complement.issubset(newpat):
                    break
                else:
                    newpat.update(complement)
            else:
                break
        return newpat

def next_closure(A, M, closure, m_i=None, stack=None):
    # print "\nNC",M, A,m_i,'::',
    if m_i is None:
        m_i = M[-1]
    for m in reversed(M):
        if m > m_i:
            continue
        
        if m in A:
            A.remove(m)
            if len(stack) > len(A)+1:
                stack.pop()
        else:
            
            B = closure(A.union([m]))
            
            # print A.union([m]),"''=",B
            if not bool(B-A) or m <= min(B-A):
                # print B
                stack.append(set([]))
                return B, m
    return M, M[-1]



def attribute_exploration_pps(tuples):
    U = range(len(tuples[0])) # Attributes
    m_prime = [set([]) for i in range(len(U))]
    g_prime = []

    representations = [[row[j] for row in tuples] for j in U]
    partitions = map(Partition.from_lst, representations)
    
    stack = [set([])]

    X = set([])
    L = []
    pc = PreClosure(L, len(U))
    m_i = U[-1]
    cycles = 0
    while X != U:
        cycles += 1
        print "\r{0: <10}".format(','.join(map(str, sorted(X)))),stack
        sys.stdout.flush()

        XJJ = closed_set(X, g_prime, m_prime)

        while X != XJJ:
            XSS = square_closure(X, partitions)
            if XJJ == XSS:
                L.append((set(X), XJJ))
                
                break
            else:
                XJJS = square(XJJ, partitions)
                XS = square(X, partitions)
                if len(XJJS) == 1 and not bool(XJJS[0]):
                    ta, tb = list(XS[0])[0:2]
                else:
                    done = False
                    for pi, pj in product(XJJS, XS):
                        if pi.issubset(pj) and len(pi) < len(pj):
                            ta = list(pj-pi)[0]
                            done = True
                            break

                    tb = list(pi)[0]
                    if not done:
                        not_singleton = reduce(set.union, XJJS)

                        for i in range(Partition.N_TUPLES):
                            if i not in not_singleton:
                                for pj in XS:
                                    if i in pj:
                                        ta = list(pj-set([i]))[0]
                                        tb = i
                                        done = True
                                        break
                            if done:
                                break
                sampled_tuple = tuple(sorted([ta,tb]))
                # for i in stack:
                #     i.add(sampled_tuple)
                gp = set([i for i, (a,b) in enumerate(zip(tuples[ta], tuples[tb])) if a==b ])
                for x in gp:
                    m_prime[x].add(len(g_prime))
                g_prime.append(gp)
                XJJ = closed_set(X, g_prime, m_prime)
        
        if not bool(XJJ-X) or m_i <= min(XJJ-X):
            m_i = U[-1]
            X = copy.copy(XJJ)
        else:
            X = set([m for m in X if m <= m_i])

        X, m_i = next_closure(X, U, pc.l_close, m_i, stack)
        stack[-1] = m_i
    for i, (ant, con) in enumerate(L):
        print '{} - {}=>{}'.format(i+1, sorted(ant), sorted(con-ant))
    print "SAMPLING CONTEXT SIZE:{}".format(len(g_prime))
    print "CYCLES:",cycles

if __name__ == "__main__":
    tuples = read_csv(sys.argv[1])

    attribute_exploration_pps(tuples)

