import json
import sys
from itertools import chain
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

    def l_close_ask(self, pat, without):
        # print 'LCLOSE', pat, self.L
        # print without
        newpat = set(pat)
        
        complement = set([])
        while True:
            if len(newpat) == self.n_atts:
                break
            subparts = [con for ri, (ant, con) in enumerate(self.L) if ri not in without and ant.issubset(newpat)]
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
    # print U
    for ant, con in pre_L:
        for x in con-ant:
            L.append((ant, set([x])))
    L.sort(key=lambda (a,c):len(a))
    
    # right-saturate
    pc = PreClosure(L, len(U))
    classes = {}
    classes_inv = {}
    for ri, (ant, con) in enumerate(L):
        ant_ask = frozenset(pc.l_close(ant))
        classes[ri] = ant_ask
        classes_inv.setdefault(ant_ask, []).append(ri)
    # print classes_inv
    
    # left-saturate
    real_L = {closed:[] for closed in classes_inv.keys()}
    new_L = FDTree(U)
    for ri, (ant, con) in enumerate(L):
        Hant = classes_inv[classes[ri]]
        
        #Hant = range(100)
        ant_circ = pc.l_close_ask(ant, Hant)
        # print ''
        # print '::', '({}=>{})'.format(ant, con),ant_circ, classes[ri], [L[i] for i in Hant]
        # print '::', '({}=>{})'.format(ant_circ, classes[ri])#, [L[i] for i in Hant]
        if ant_circ != classes[ri]:
            if not any(previous.issubset(ant_circ) for previous in real_L[classes[ri]] ):
                for x in range(len(real_L[classes[ri]])-1, -1, -1):
                    if ant_circ.issubset(real_L[classes[ri]][x]):

                        del real_L[classes[ri]][x]
                real_L[classes[ri]].append(ant_circ)
            # elif classes[ri].issubset(real_L[classes[ri]]):
            #     real_L[classes[ri]] = ant_circ

    real_L = [[(ant, con) for ant in ants] for con, ants in real_L.items() if bool(ants)]
    print len(list(chain(*real_L)))

        # for ri, (pant, pcon) in enumerate(L):
            # if ri not in Hant and pant.issubset(ant):
                # print '\t', pant, con, ant
        


    
    