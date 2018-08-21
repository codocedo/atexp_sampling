from itertools import combinations
from math import factorial as fac
from ae_libs.boolean_tree import BooleanTree

def binomial(x, y):
    try:
        binom = fac(x) // fac(y) // fac(x - y)
    except ValueError:
        binom = 0
    return binom
'''
************************************************************************************************
HANDLES THE KIND OF REPRESENTATION
************************************************************************************************
'''
class Top(object):
    @staticmethod
    def intersection(other):
        return other
    @staticmethod
    def add(obj):
        pass
    @staticmethod
    def is_empty():
        return False

class Representation(object):
    '''
    Abstract representation
    '''
    def __init__(self, desc):
        self.desc = desc
    def intersection(self, other):
        raise NotImplementedError
    def leq(self, other):
        raise NotImplementedError
    def sample(self, lst):
        raise NotImplementedError
    def __repr__(self):
        return str(self.desc)
    def __sub__(self, other):
        raise NotImplementedError
    def pick_sample_from_difference(self, other, samples):
        raise NotImplementedError
    def add(self, value):
        self.desc.add(value)

class Partition(Representation):
    '''
    Partiton representation, split partitions
    list of sets
    '''
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
        
    def set_idx(self, idx):
        self.idx = idx

    @staticmethod
    def from_lst( lst):
        hashes = {}
        for i, j in enumerate(lst):
            hashes.setdefault(j, set([])).add(i)
        return Partition(hashes.values())

    def intersection(self, other):
        '''
        Procedure STRIPPED_PRODUCT defined in [1]
        '''
        new_desc = []
        T = {}
        S = {}
        for i, k in enumerate(self.desc):
            for t in k:
                T[t] = i
            S[i] = set([])
        for i, k in enumerate(other.desc):
            for t in k:
                if T.get(t, None) is not None:
                    S[T[t]].add(t)
            for t in k:
                if T.get(t, None) is not None:
                    if len(S[T[t]]) > 1:
                        new_desc.append(S[T[t]])
                    S[T[t]] = set([])
        return Partition(new_desc)
    def leq(self, other):
        for i in self.desc:
            if not any(i.issubset(j) for j in other.desc):
                return False
        return True

    def sample(self, sample):
        # print self, sample,
        sampled = set([])
        for i, j in sample:
            for s in self.desc:
                if i in s and j in s:
                    sampled.add((i,j))
                    break
        # print sampled
        return sampled
        # return PairSet(self.desc.intersection(sample))
    def pick_sample_from_difference(self, other, samples):
        # print "PICK", self, other, samples
        
        for s1 in self.desc:
            for i, j in combinations(s1, 2):
                if any(i in s2 and j in s2 for s2 in other.desc):
                    continue
                else:
                    t = (i,j) if i<j else (j,i)
                    samples.append(t)
                    return t
        # print samples
        # exit()
        # samples.append(next(iter(self.desc - other.desc)))
    def is_empty(self):
        return len(self.desc) == 1 and len(self.desc[0]) == 0

    def __eq__(self, other):
        if len(self.desc) != len(other.desc):
            return False
        for s in self.desc:
            if any(s == j for j in other.desc):
                continue
            else:
                return False
        return True
    

class PairSet(Representation):
    '''
    Pairset representation, set of tuple pairs
    '''
    @staticmethod
    def from_lst(lst):
        '''
        Generates the set of pairs from a list of elements
        [1,2,1,2] generates the pairs [(0,2), (1,3)]
        Actually, pairs are the transitive closure of the equivalence relation
        '''
        hashes = {}
        for i, j in enumerate(lst):
            hashes.setdefault(j, set([])).add(i)
        desc = set([])
        for val in hashes.values():
            map(desc.add, combinations(sorted(val), 2))
        return PairSet(desc)
        

    def intersection(self, other):
        return PairSet(self.desc.intersection(other.desc))
    def leq(self, other):
        return self.desc.issubset(other.desc)

    def sample(self, sample):
        return PairSet(self.desc.intersection(sample))

    def pick_sample_from_difference(self, other, samples):
        samples.append(next(iter(self.desc - other.desc)))
        
    


'''
************************************************************************************************
HANDLES THE DATABASE AND SAMPLING
************************************************************************************************
'''


class Database(object):
    def __init__(self):
        self._data = None
        self._partitions = None
        self._ps = None
        self._atts = None
        self._ctx = None
        self._n_tuples = None
        self.TRep = PairSet
        
        # self._representation_method = lst_to_pairs
        # self._representation_method = lst_to_partitions
    @property
    def n_atts(self):
        return len(self.ctx)

    @property
    def n_tuples(self):
        if self._n_tuples is None:
            self._n_tuples = len(self._data)
        return self._n_tuples

    def read_csv(self, path, separator=','):
        '''
        Read csv into self._data
        self._data contains the original parsed file
        '''
        self._data = [map(str, line.replace('\n','').split(separator)) for line in open(path, 'r').readlines()]

    @property
    def ctx(self):
        '''
        Returns the context and builds it if its not been built yet.
        The context is simply the self._data transposed
        '''
        if self._ctx is None:
            self._ctx = [[row[j] for row in self._data] for j in range(len(self._data[0]))]
        return self._ctx

    @property
    def partitions(self):
        '''
        Builds the partitions from the context
        partitions can be either a list of pairs or a list of sets.
        '''
        if self._partitions is None:
            self._partitions = [self.TRep.from_lst(j) for j in self.ctx]
            # self._partitions = [filter(lambda x:len(x)>1, lst_to_pairs(j)) for j in self.ctx]
        # print self._partitions
        return self._partitions

    @property
    def ps(self):
        if self._ps is None:
            self._ps =  {i: j for i, j in enumerate(self.partitions)}
        return self._ps

    @property
    def atts(self):
        if self._atts is None:
            self._atts = range(len(self.ctx))
        return self._atts

import random
class Expert(Database):
    def __init__(self, stack, split=1.0):
        Database.__init__(self)
        self.sample = set([])
        self._real_ps = None
        self.increments = 0
        self.split = split
        self._smap = None
        self.TExpert = Partition
        self.stack = stack

    @property
    def sample_map(self):
        if self._smap is None:
            self._smap = list(range(self.n_tuples))
            random.shuffle(self._smap)
        return self._smap

    
    def get_next_pair(self):
        for i, j in combinations(list(range(self.n_tuples)), 2):
            
            yield (self.sample_map[i], self.sample_map[j]) if self.sample_map[i] < self.sample_map[j] else (self.sample_map[j], self.sample_map[i])

    @property
    def partitions(self):
        '''
        Builds the partitions from the context
        partitions can be either a list of pairs or a list of sets.
        '''
        if self._partitions is None:
            self._partitions = [self.TExpert.from_lst(j) for j in self.ctx]
            # self._partitions = [filter(lambda x:len(x)>1, lst_to_pairs(j)) for j in self.ctx]
        # print self._partitions
        return self._partitions

    @property
    def ps(self):
        '''
        Returns the sampeld object representations
        '''
        if self._ps is None:
            self.possible_pairs = binomial(self.n_tuples, 2)
            self.sample_size = int(self.possible_pairs*self.split)
            self.sample = []
            for pi, pair in enumerate(self.get_next_pair()):
                if pi == self.sample_size:
                    break
                self.sample.append(pair)

            self._real_ps = {i: j for i, j in enumerate(self.partitions)}
            
            self._ps =  {i: self.TRep(j.sample(self.sample)) for i, j in enumerate(self.partitions)}

        return self._ps
    

    def check_bk(self, preintent, preextent):        
        new_extent = reduce(lambda x, y: x.intersection(y), (self._real_ps[i] for i in preintent)) #A^I
        new_intent = set([i for i, j in self._real_ps.items() if i not in preintent and new_extent.leq(j)]) # A^II
        new_intent.update(preintent)
        return new_intent, new_extent

    def check(self, new_att, prevint, closed_preintent, prevAI):

        if prevAI.is_empty():
            '''
            Search up the stack if there is a pattern we can partially use
            to calculate the current one. In the worst case, we will always
            use the top.
            '''
            for idx in range(len(self.stack)-1, -1, -1):
                if not self.stack[idx][2].is_empty():
                    break
            prevAI.desc = self.stack[idx][2].intersection(
                reduce(
                    lambda x, y: x.intersection(y),
                    (self._real_ps[i] for i in prevint if i not in self.stack[idx][0])
                )
            ).desc #A^I

        AI = prevAI.intersection(self._real_ps[new_att])
        AII = set([j for j in closed_preintent if AI.leq(self._real_ps[j])]) # A^II
        return AII, AI

        
    def increment_sample(self, AI, AII, closed_preintent, preintent):
        
        self.increments += 1

        sample_target = next(iter(closed_preintent - AII))
        new_point = None
        for s1 in reversed(AI.desc):
            for i, j in combinations(s1, 2):
                if any(i in s2 and j in s2 for s2 in reversed(self._real_ps[sample_target].desc)):
                    continue
                else:
                    new_point = (i,j) if i<j else (j,i)
                    break
            if new_point is not None:
                break
        
        self.sample.append(new_point)
        self._ps =  {i: self.TRep(j.sample(self.sample)) for i, j in enumerate(self.partitions)}
        
        return new_point



class ExpertSampler(Expert):
    def __init__(self, stack, split=1.0):
        super(ExpertSampler, self).__init__(stack, split)
        self.non_fds = BooleanTree()
    def increment_sample(self, AI, AII, closed_preintent, preintent):
        t1, t2 = super(ExpertSampler, self).increment_sample(AI, AII, closed_preintent, preintent)
        match = [self._data[t1][i]==self._data[t2][i] for i in range(self.n_atts)]
        self.non_fds.append(match)
        return (t1, t2)
    

    @property
    def partitions(self):
        '''
        Builds the partitions from the context
        partitions can be either a list of pairs or a list of sets.
        '''
        if self._partitions is None:
            self._partitions = [self.TExpert.from_lst(j) for j in self.ctx]
            map(lambda (i, p): p.set_idx(i), enumerate(self._partitions))
            orden = lambda p: (self._n_tuples-sum([len(j) for j in p.desc]))+len(p.desc)
            # print [orden(p) for p in self._partitions]
            self._partitions.sort(key=orden)
            for ti, t in enumerate(self._data):
                new_t = [None]*len(t)
                # print t
                for i, j in enumerate(t):
                    # print '\t', self._partitions[i].idx, '=>', i , ':', j
                    new_t[i] = t[self._partitions[i].idx]
                for i, j in enumerate(new_t):
                    self._data[ti][i] = j
                # print t
                # print ''
            # print [(orden(p), p.idx) for p in self._partitions]
            # print self._partitions
            # exit()
            # self._partitions = [filter(lambda x:len(x)>1, lst_to_pairs(j)) for j in self.ctx]
        # print self._partitions
        return self._partitions