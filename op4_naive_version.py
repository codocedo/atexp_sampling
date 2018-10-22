## OPTIMIZATION 1NAIVE VERSION
# USES STRIPED PARTITIONS
# USES A STACK
# USES ORDERED PARTITIONS



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
        return Partition.top()#[reduce(set.union, partitions[0])]

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

class FormalContext(object):
    def __init__(self, g_prime, m_prime):
        self.g_prime = g_prime
        self.m_prime = m_prime

    def derive_intent(self, intent):
        '''
        returns intent'
        '''
        if bool(intent):
            out = reduce(set.intersection, [self.m_prime[x] for x in intent])
            if len(intent) == 1:
                out = copy.copy(out)
            return out
        return set(range(len(self.g_prime)))

    def derive_extent(self, extent):
        '''
        return extent'
        '''
        if bool(extent):
            out = reduce(set.intersection, [self.g_prime[t] for t in extent])    
            if len(extent) == 1:
                out = copy.copy(out)
            return out
        return set(range(len(self.m_prime)))

        

    def closed_set(self, X):
        return self.derive_extent(self.derive_intent(X))
    
    

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
    # print "\nNC" ,m_i,'::',
    if m_i is None:
        m_i = M[-1]
    for m in reversed(M):
        if m > m_i:
            continue
        
        if m in A:
            A.remove(m)
            if m == stack[-1][0]:
                stack.pop()
        else:
            
            B = closure(A.union([m]))
            
            # print A.union([m]),"''=",B
            if not bool(B-A) or m <= min(B-A):
                # print B
                stack.append([None,set([]), None])
                return B, m
    return M, M[-1]

def sampling(XJJS, XS):
    if len(XJJS) == 1 and not bool(XJJS[0]): # IF XJJS IS THE TOP
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
    return tuple(sorted([ta,tb]))

def attribute_exploration_pps(tuples):
    U = range(len(tuples[0])) # Attributes
    m_prime = [set([]) for i in range(len(U))]
    g_prime = []

    fctx = FormalContext(g_prime, m_prime)

    representations = [[row[j] for row in tuples] for j in U]

    # ORDERING
    order = [(len(set(r)), ri) for ri, r in enumerate(representations)]
    order.sort(key=lambda k: k[0], reverse=False)
    print order
    order = {j[1]:i for i,j in enumerate(order)} #Original order -> new order
    inv_order = {i:j for j,i in order.items()}
    for ti, t in enumerate(tuples):
        tuples[ti] = [t[inv_order[i]] for i in range(len(t))]
    
    # END ORDERING
    representations = [[row[j] for row in tuples] for j in U]
    partitions = map(Partition.from_lst, representations)

    stack = [[None, None, None],[None, set([]), Partition.top()]]

    X = set([])
    L = []
    pc = PreClosure(L, len(U))
    m_i = None
    cycles = 0
    XJ = set([])
    XJJ = fctx.closed_set(X)
    while X != U:
        cycles += 1
        print "\r{0: <10}".format(','.join(map(str, sorted(X)))),#stack
        sys.stdout.flush()
        
        if m_i is not None:
            XJ = stack[-2][1].intersection(m_prime[m_i])
            XJJ = fctx.derive_extent(XJ)

        XSS = None
        XS = None
        while X != XJJ:
            if XSS is None:
                if stack[-2][2] is not None:
                    XS = Partition.intersection(stack[-2][2], partitions[m_i])
                else:
                    si = len(stack)
                    for si in range(len(stack)-2, 0, -1):
                        if stack[si][2] is not None:
                            break
                    for i in range(si+1, len(stack)-1):
                        stack[i][2] = Partition.intersection(stack[i-1][2], partitions[stack[i][0]])
                    if m_i is not None:
                        XS = Partition.intersection(stack[-2][2], partitions[m_i])
                    else:
                        XS = square(X, partitions)
                XSS = X.union([m for m in XJJ-X if Partition.leq(XS, partitions[m])])
                # XSS = set([i for i, p in enumerate(partitions) if Partition.leq(XS, p)])
            if XJJ == XSS:
                L.append((set(X), set(XJJ)))                
                break
            else:
                XJJS = reduce(Partition.intersection, [partitions[x] for x in XJJ-XSS]+[XS])
                sampled_tuple = sampling(XJJS, XS)

                XJ.add(len(g_prime))

                for i in stack[1:]:
                    i[1].add(len(g_prime))
                
                gp = set([i for i, (a,b) in enumerate(zip(tuples[sampled_tuple[0]], tuples[sampled_tuple[1]])) if a==b ])
                for x in gp:
                    m_prime[x].add(len(g_prime))
                g_prime.append(gp)
                
                XJJ.intersection_update(gp)# = fctx.closed_set(X)
                # print XJJ, XSS, fctx.closed_set(X), gp

        
        if not bool(XJJ-X) or m_i <= min(XJJ-X):
            m_i = U[-1]
            X = XJJ
        else:
            X.difference_update([m for m in X if m > m_i])

        stack[-1][1] = XJ
        stack[-1][2] = XS
        X, m_i = next_closure(X, U, pc.l_close, m_i, stack)
        # print stack
        stack[-1][0] = m_i
    # for i, (ant, con) in enumerate(L):
    #     print '{} - {}=>{}'.format(i+1, sorted(ant), sorted(con-ant))
    print "\nN_FDS:{}".format(len(L))
    print "SAMPLING CONTEXT SIZE:{}".format(len(g_prime))
    print "CYCLES:",cycles

if __name__ == "__main__":
    tuples = read_csv(sys.argv[1])

    attribute_exploration_pps(tuples)

