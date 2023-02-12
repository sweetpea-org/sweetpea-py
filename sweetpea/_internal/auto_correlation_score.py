import random


def convert_samples(samples: list) -> list:
    """Convert string levels in a sample to numbers"""
    factors = set()
    ### get factors
    for s in samples:
        for f in s.keys():
            factors.add(f)
    factor_dict = {}
    ### get the level dict for every factor:

    for s in samples:
        for f in factors:
            item = set()
            for l in s[f]:
                item.add(l)
            item_ = list(item)
            factor_dict[f] = {item_[i]: float(i) for i in range(len(item_))}
    res = []
    for s in samples:
        s_ = {}
        for k in s.keys():
            s_[k] = [factor_dict[k][l] for l in s[k]]
        res.append(s_)
    return res


def train_test_split_samples(samples: list, percentage: float = .8) -> tuple:
    """split list of samples in train and test samples"""
    samples_ = samples.copy()
    random.shuffle(samples_)
    split = int(percentage * len(samples_))
    if split == 0 or split == len(samples_):
        raise Exception('Train or test set empty')
    return samples_[:split], samples_[split:]


def create_x_y_sample(sample: dict, y_factor: str, k: int = 10) -> tuple:
    """create the independent and dependent values in a sample"""
    x_lists = []
    y_list = sample[y_factor]
    for key in sample.keys():
        x_lists.append(sample[key])
    k_ = min(len(y_list) // 2, k)
    start = 0
    end = k_
    x_res = []
    y_res = []
    if len(y_list) < k_:
        raise Exception('predict distance to high in auto correlation test')
    while end < len(y_list):
        x_temp = []
        for x in x_lists:
            x_temp += x[start: end]
        x_res.append(x_temp)
        y_res.append(y_list[end])
        start += 1
        end += 1
    return x_res, y_res


def create_x_y_train_test_samples(samples: list, factor: str, percentage: float = .8, k: int = 10) -> tuple:
    """create a list of train independent, train dependent, test independent and test dpendent variables"""
    train_set, test_set = train_test_split_samples(samples, percentage)
    x_train = []
    y_train = []
    x_test = []
    y_test = []
    for s in train_set:
        x_train_, y_train_ = create_x_y_sample(s, factor, k)
        x_train += x_train_
        y_train += y_train_
    for s in test_set:
        x_test_, y_test_ = create_x_y_sample(s, factor, k)
        x_test += x_test_
        y_test += y_test_
    return x_train, y_train, x_test, y_test


def auto_correlation_score_factor(samples: list, factor: str, percentage: float = .8, k: int = 10) -> float:
    """get the auto correlation score for a single factor"""
    try:
        from sklearn.neural_network import MLPClassifier
    except ImportError as e:
        raise Exception('To use a auto correlation test, please install the sklearn package: pip install sklearn\n')
    samples_converted = convert_samples(samples)
    x_train, y_train, x_test, y_test = create_x_y_train_test_samples(samples_converted, factor, percentage, k)
    clf = MLPClassifier(solver='lbfgs', alpha=1e-5, hidden_layer_sizes=(15,), random_state=1)
    clf.fit(x_train, y_train)
    return clf.score(x_test, y_test)

