## NAIVE VERSION

import csv
import sys
from ae_libs.enumerations import LectiveEnum
from itertools import product

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
        return reduce(intersect_partitions, [partitions[x] for x in X])
    else:
        return [reduce(set.union, partitions[0])]

def square_closure(X, partitions):
    pattern = square(X, partitions)
    return set([i for i, p in enumerate(partitions) if leq_partitions(pattern, p)])

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

def next_closure(A, M, closure):
    for m in reversed(M):
        if m in A:
            A.remove(m)
        else:
            
            B = closure(A.union([m]))
            # print A.union([m]),"''=",B
            if not bool(B-A) or m <= min(B-A):
                return B
    return M



def attribute_exploration_pps(tuples):
    U = range(len(tuples[0])) # Attributes
    m_prime = [set([]) for i in range(len(U))]
    g_prime = []

    representations = [[row[j] for row in tuples] for j in U]
    partitions = map(make_partition_from_list, representations)
    
    # g_prime, m_prime, tuples = sampling_context
    # enum = LectiveEnum(len(M)-1)

    X = set([])
    L = []
    pc = PreClosure(L, len(U))

    while X != U:
        print "\r****",X,
        sys.stdout.flush()
        XJJ = closed_set(X, g_prime, m_prime)
        while X != XJJ:
            
            XSS = square_closure(X, partitions)
            # print X, XJJ, XSS
            if XJJ == XSS:
                L.append((set(X), XJJ))
                # print "\nNEWFD {}=>{} | {}\n".format(X, XJJ, L)
                break
            else:
                XJJS = square(XJJ, partitions)
                XS = square(X, partitions)
                # print '--'*50
                
                # print XJJS
                # print XS
                for pi, pj in product(XJJS, XS):
                    # print '\t\tpi',pi
                    # print '\t\t\tpj',pj
                    if pi.issubset(pj) and len(pi) < len(pj):
                        ta = list(pj-pi)[0]
                        break
                tb = list(pi)[0]
                # print "CHOSE:",ta, tb
                gp = set([i for i, (a,b) in enumerate(zip(tuples[ta], tuples[tb])) if a==b ])
                for x in gp:
                    m_prime[x].add(len(g_prime))
                g_prime.append(gp)
                XJJ = closed_set(X, g_prime, m_prime)
                
                # print '\t->',XJJ, g_prime, m_prime
        # print "NC", X
        X = next_closure(X, U, pc.l_close)
    for i, (ant, con) in enumerate(L):
        print '{} - {}=>{}'.format(i+1, sorted(ant), sorted(con-ant))
    print "SAMPLING CONTEXT SIZE:{}".format(len(g_prime))

if __name__ == "__main__":
    tuples = read_csv(sys.argv[1])

    attribute_exploration_pps(tuples)

