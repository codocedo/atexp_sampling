import json
import sys
from ae_libs.fd_tree import FDTree

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

    def l_close_ask(self, pat, without):
        # print 'LCLOSE', pat, self.L
        newpat = set(pat)
        
        complement = set([])
        while True:
            if len(newpat) == self.n_atts:
                break
            subparts = [con for ri, (ant, con) in enumerate(self.L) if ri not in without and len(ant) < len(newpat) and ant.issubset(newpat)]
            if bool(subparts):
                complement = reduce(set.union, subparts)
                if complement.issubset(newpat):
                    break
                else:
                    newpat.update(complement)
            else:
                break
        return newpat

def read_rules(path):
    with open(path, 'r') as fin:
        fds = []
        for ri, (ant, con) in enumerate(json.load(fin)):
            fds.append((set(ant), set(con)))
        return fds

if __name__ == "__main__":
    pre_L = read_rules(sys.argv[1])
    U = reduce(set.union, [i[0].union(i[1]) for i in pre_L])
    L = []
    print U
    for ant, con in pre_L:
        for x in con-ant:
            L.append((ant, set([x])))
            
    # right-saturate
    pc = PreClosure(L, len(U))
    classes = {}
    classes_inv = {}
    for ri, (ant, con) in enumerate(L):
        ant_ask = frozenset(pc.l_close(ant))
        classes.setdefault(ri, []).append(ant_ask)
        classes_inv.setdefault(ant_ask, []).append(ri)
    print classes_inv
    
    # left-saturate
    new_L = FDTree(U)
    for ri, (ant, con) in enumerate(L):
        Hant = classes[ri]
        pc.l_close_ask(ant, Hant)
        


    
    