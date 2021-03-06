import numpy as np
import hippo.io
import hippo.query
import h5py

NUM_SENTENCES = 16
NUM_REPS = {'krns2': 15, 'PassAct2': 10, 'PassAct3': 10}
VALID_SUBS = {'krns2': ['B', 'C', 'D', 'E', 'F', 'G', 'H'],
              'PassAct2': ['A', 'B', 'C'],
              'PassAct3': ['A', 'B', 'C', 'E', 'F', 'G', 'J', 'K', 'L', 'N', 'O', 'R', 'S', 'T', 'V', 'X', 'Y', 'Z']}

WORD_INDS = {'firstNoun': 0, 'verb': 1, 'secondNoun': 2}

WORD_POS = {'active':
                {'firstNoun': 1,
                 'verb': 2,
                 'secondNoun': 4},
            'passive':
                {'firstNoun': 1,
                 'verb': 3,
                 'secondNoun': 6}}


WORD_PER_SEN = {'krns2':
                    {'active':
                         {'firstNoun': ['doctor','dog','monkey','student'],
                          'verb': ['found', 'kicked','inspected','touched'],
                          'secondNoun': ['peach.','hammer.','school.','door.']},
                     'passive':
                         {'firstNoun': ['peach','hammer','school','door'],
                          'verb': ['found', 'kicked', 'inspected', 'touched'],
                          'secondNoun': ['doctor.', 'dog.', 'monkey.', 'student.']}},
                'PassAct2':
                    {'active':
                         {'firstNoun': ['man', 'girl', 'woman', 'boy'],
                          'verb': ['watched', 'liked', 'despised', 'encouraged'],
                          'secondNoun': ['man.', 'girl.', 'woman.', 'boy.']},
                     'passive':
                         {'firstNoun': ['man', 'girl', 'woman', 'boy'],
                          'verb': ['watched', 'liked', 'despised', 'encouraged'],
                          'secondNoun': ['man.', 'girl.', 'woman.', 'boy.']}},
                'PassAct3':
                    {'active':
                         {'firstNoun': ['man', 'girl', 'woman', 'boy'],
                          'verb': ['kicked', 'helped', 'approached', 'punched'],
                          'secondNoun': ['man.', 'girl.', 'woman.', 'boy.']},
                     'passive':
                         {'firstNoun': ['man', 'girl', 'woman', 'boy'],
                          'verb': ['kicked', 'helped', 'approached', 'punched'],
                          'secondNoun': ['man.', 'girl.', 'woman.', 'boy.']}}}
'''
In Nicole's experiments she is using some context before and after the word, therefore there is -0.5 in tmin and 4 in tmax
I should be using tmin = 0 and tmax = 0.4
TIME_LIMITS = {'active': {'firstNoun': {'tmin': -0.5, 'tmax': 4.5},
                          'verb': {'tmin': -0.5, 'tmax': 4},
                          'secondNoun': {'tmin': -0.5, 'tmax': 3}},
               'passive': {'firstNoun': {'tmin': -0.5, 'tmax': 5.5},
                           'verb': {'tmin': -0.5, 'tmax': 4.5},
                           'secondNoun': {'tmin': -0.5, 'tmax': 4}}}
'''
TIME_LIMITS = {'active': {'firstNoun': {'tmin': -0.5, 'tmax': 4.5},
                          'verb': {'tmin': 0.0, 'tmax': 0.4},
                          'secondNoun': {'tmin': -0.5, 'tmax': 3}},
               'passive': {'firstNoun': {'tmin': -0.5, 'tmax': 5.5},
                           'verb': {'tmin': 0.0, 'tmax': 0.4},
                           'secondNoun': {'tmin': -0.5, 'tmax': 4}}}

# Old slugs:
# 'trans-D_nsb-5_cb-0_empty-4-10-2-2_band-1-150_notch-60-120_beats-head-meas_blinks-head-meas'
# 'sss_emptyroom-4-10-2-2_band-1-150_notch-60-120_beatremoval-first_blinkremoval-first'
# 'trans-D_nsb-5_cb-0_emptyroom-4-10-2-2_band-5-150_notch-60-120_beatremoval-first_blinkremoval-first'
DEFAULT_PROC = 'trans-D_nsb-5_cb-0_empty-4-10-2-2_band-1-150_notch-60-120_beats-head-meas_blinks-head-meas'
PDTW_FILE = '/share/volume0/newmeg/{exp}/avg/{exp}_{sub}_{proc}_parsed_{word}_pdtwSyn.mat'


def load_pdtw(subject, word, experiment='krns2', proc=DEFAULT_PROC):
    fname = PDTW_FILE.format(exp=experiment, sub=subject, proc=proc, word=word)
    loadVars = h5py.File(fname)

    time_a = np.array(loadVars[u'fullTime_a'])
    time_p = np.array(loadVars[u'fullTime_p'])

    fullWordLab = loadVars[u'fullWordLab']
    labels = fullWordLab[WORD_INDS[word], :]

    active_data_raw = np.transpose(loadVars[u'activeData'], axes=(2, 1, 0))
    passive_data_raw = np.transpose(loadVars[u'passiveData'], axes=(2, 1, 0))

    return time_a, time_p, labels, active_data_raw, passive_data_raw


def load_raw(subject, word, sen_type, experiment='krns2', proc=DEFAULT_PROC):
    usis = hippo.query.query_usis([('stimuli_set', experiment),
                                   ('stimulus', lambda s: s in WORD_PER_SEN[experiment][sen_type][word]),
                                   # without periods, gets the first noun
                                   ('sentence_id', lambda sid: sid != None),
                                   ('word_index_in_sentence', lambda wis: wis == WORD_POS[sen_type][word])],
                                  include_annotations=['stimulus', 'sentence_id'])  # excludes questions
    exp_sub = [(experiment, subject)]
    uels = hippo.query.get_uels_from_usis(usis.keys(), experiment_subjects=exp_sub)
    uels = {k: v for (k, v) in uels.iteritems() if len(v) > 0}  # checking for empties
    id_uels = [(k, uels[k]) for k in uels.keys()]  # putting uels in a list instead of a map (explicit ordering)
    labels = [usis[k]['stimulus'] for k, _ in id_uels]

    _, uels = zip(*id_uels)

    tmin = TIME_LIMITS[sen_type][word]['tmin']
    tmax = TIME_LIMITS[sen_type][word]['tmax']
    evokeds = np.array([hippo.io.load_mne_epochs(us, preprocessing=proc, baseline=None,
                                        tmin=tmin, tmax=tmax) for us in uels])

    # Downsample, check if this is necessary, nichole's experiment showed that not all points are necessary, but I could keep them and check
    # evokeds = evokeds[:, :, :, ::2]
    # time = np.arange(tmin, tmax+2e-3, 2e-3)
    time = np.arange(tmin, tmax+1e-3, 1e-3)
    print(evokeds.shape[3])
    print(time.size)
    assert evokeds.shape[3] == time.size

    return evokeds, labels, time

def load_full_experiment(subject, word, sen_type, experiment='krns2', proc=DEFAULT_PROC):
    usis = hippo.query.query_usis([('stimuli_set', experiment),
                                   ('stimulus', lambda s: s in WORD_PER_SEN[experiment][sen_type][word]),
                                   # without periods, gets the first noun
                                   ('sentence_id', lambda sid: sid != None),
                                   ('word_index_in_sentence', lambda wis: wis == WORD_POS[sen_type][word])],
                                  include_annotations=['stimulus', 'sentence_id'])  # excludes questions
    exp_sub = [(experiment, subject)]
    uels = hippo.query.get_uels_from_usis(usis.keys(), experiment_subjects=exp_sub)
    uels = {k: v for (k, v) in uels.iteritems() if len(v) > 0}  # checking for empties
    id_uels = [(k, uels[k]) for k in uels.keys()]  # putting uels in a list instead of a map (explicit ordering)
    labels = [usis[k]['stimulus'] for k, _ in id_uels]
    sentence_id = [usis[k]['sentence_id'] for k, _ in id_uels]
    _, uels = zip(*id_uels)

    tmin= 0.0;tmax=3.9
    evokeds = np.array([hippo.io.load_mne_epochs(us, preprocessing=proc, baseline=None,
                                        tmin=tmin, tmax=tmax) for us in uels])

    # Downsample, check if this is necessary, nichole's experiment showed that not all points are necessary, but I could keep them and check
    # evokeds = evokeds[:, :, :, ::2]
    # time = np.arange(tmin, tmax+2e-3, 2e-3)
    time = np.arange(tmin, tmax+1e-3, 1e-3)
    print(evokeds.shape[3])
    print(time.size)
    assert evokeds.shape[3] == time.size

    return evokeds, labels, sentence_id, time

def load_raw_all_verbs(proc=DEFAULT_PROC):
    usis = hippo.query.query_usis([('stanford_2017_06_09_pos',lambda s : s.startswith('VB')),('sentence_id', lambda sid : sid != None)], include_annotations=['stimulus', 'sentence_id'])
    uels = hippo.query.get_uels_from_usis(usis.keys())
    uels = {k: v for (k, v) in uels.iteritems() if len(v) > 0}  # checking for empties
    id_uels = [(k, uels[k]) for k in uels.keys()]  # putting uels in a list instead of a map (explicit ordering)
    labels = [usis[k]['stimulus'] for k, _ in id_uels]

    _, uels = zip(*id_uels)

    tmin = 0.0#TIME_LIMITS[sen_type][word]['tmin']
    tmax = 0.4#TIME_LIMITS[sen_type][word]['tmax']
    evokeds = np.array([hippo.io.load_mne_epochs(us, preprocessing=proc, baseline=None,
                                        tmin=tmin, tmax=tmax) for us in uels])

    # Downsample, check if this is necessary, nichole's experiment showed that not all points are necessary, but I could keep them and check
    # evokeds = evokeds[:, :, :, ::2]
    # time = np.arange(tmin, tmax+2e-3, 2e-3)
    time = np.arange(tmin, tmax+1e-3, 1e-3)
    print(evokeds.shape[3])
    print(time.size)
    assert evokeds.shape[3] == time.size

    return evokeds, labels, time

def avg_data_all(data_raw, labels_raw,num_instances=1, reps_to_use=-1):
    
    if len(data_raw.shape) > 3:
        data_list = []
        for i in range(num_instances):
            data_list.append(np.mean(data_raw[:, range(i, reps_to_use, num_instances), :, :], axis=1))
        data = np.concatenate(data_list, axis=0)
    else:
        data = np.empty((NUM_SENTENCES * num_instances, data_raw.shape[1], data_raw.shape[2]))
        for s in range(NUM_SENTENCES):
            startInd = num_reps * s
            endInd = startInd + reps_to_use - 1
            for i in range(num_instances):
                data[s + (NUM_SENTENCES*i), :, :] = np.mean(data_raw[(startInd + i):endInd:num_instances, :, :], axis=0)

    labels = []
    for i in range(num_instances):
        labels.extend(labels_raw)

    return data, labels

def avg_data(data_raw, labels_raw, experiment='krns2', num_instances=2, reps_to_use=-1):
    num_reps = NUM_REPS[experiment]
    if reps_to_use == -1:
        reps_to_use = num_reps

    if len(data_raw.shape) > 3:
        data_list = []
        for i in range(num_instances):
            data_list.append(np.mean(data_raw[:, range(i, reps_to_use, num_instances), :, :], axis=1))
        data = np.concatenate(data_list, axis=0)
    else:
        data = np.empty((NUM_SENTENCES * num_instances, data_raw.shape[1], data_raw.shape[2]))
        for s in range(NUM_SENTENCES):
            startInd = num_reps * s
            endInd = startInd + reps_to_use - 1
            for i in range(num_instances):
                data[s + (NUM_SENTENCES*i), :, :] = np.mean(data_raw[(startInd + i):endInd:num_instances, :, :], axis=0)

    labels = []
    for i in range(num_instances):
        labels.extend(labels_raw)

    return data, labels


