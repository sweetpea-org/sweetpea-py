from sweetpea import SMGen

def maybe_unique(experiments, gen):
    if gen != SMGen:
        return experiments
    def first(tup):
        return tup[0]
    def hashable(d):
        trials = [(key, tuple(d[key])) for key in d]
        trials.sort(key=first)
        return tuple(trials)
    return list(set([hashable(exp) for exp in experiments]))
