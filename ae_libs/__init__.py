import csv

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

def match(t1, t2, tuples):
    return set([i for i, (a,b) in enumerate(zip(tuples[t1], tuples[t2])) if a==b ])