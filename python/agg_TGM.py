import argparse
import load_data
import numpy as np
import os
import re
import run_TGM


PARAMS_TO_AGG = ['w', 'o', 'pd', 'pr', 'F', 'alg', 'z', 'avg', 'ni', 'nr', 'rs']
PARAM_TYPES = {'w':'\d+',
               'o':'\d+',
               'pd':['T', 'F'],
               'pr':['T', 'F'],
               'F':'\d+',
               'alg':['LR', 'GNB'],
               'z':['T', 'F'],
               'avg':['T', 'F'],
               'ni':'\d+',
               'nr':'\d+',
               'rs':'\d+'}


def which_word(fname):
    if 'firstNoun' in fname:
        return 'firstNoun'
    elif 'verb' in fname:
        return 'verb'
    elif 'secondNoun' in fname:
        return 'secondNoun'
    else:
        raise ValueError('Invalid fname')


def which_sen_type(fname):
    if 'active' in fname:
        return 'active'
    elif 'passive' in fname:
        return 'passive'
    else:
        raise ValueError('Invalid fname')


def extract_param(param_name, fname):
    print(param_name)
    if param_name == 'alg':
        for alg in PARAM_TYPES[param_name]:
            if alg in fname:
                return alg
        raise ValueError('Invalid fname')
    if param_name == 'F':
        m = re.match('.*_(\d+)F_.*', fname)
        if m:
            return m.group(1)
        else:
            raise ValueError('Invalid fname')
    if isinstance(PARAM_TYPES[param_name], list):
        for val in PARAM_TYPES[param_name]:
            if param_name + val in fname:
                return val
        raise ValueError('Invalid fname')

    match_str = '_{}(\d+)_'.format(param_name)
    m = re.match('.*_' + param_name + '(\d+)_.*', fname)
    if m:
        return m.group(1)
    else:
        raise ValueError('Invalid fname')

def get_param_str(param_name, param_val):
    if param_name == 'alg':
        return param_val
    if param_name == 'F':
        return '_{}F_'.format(param_val)
    if isinstance(PARAM_TYPES[param_name], list):
        return param_name + param_val

    return '_{}{}_'.format(param_name, param_val)


def tgm_from_preds(preds, l_index, cv_membership, accuracy='abs'):
    print(preds.shape)
    print(l_index)
    print(cv_membership.shape)


def agg_results(exp, mode, accuracy, sub, param_specs=None):
    sub_results = {}
    sub_params = {}
    sub_time = {}
    result_dir = run_TGM.SAVE_DIR.format(exp=exp, sub=sub)
    result_files = os.listdir(result_dir)
    for f in result_files:
        valid_file = mode in f
        if param_specs is not None:
            for param_name, param_val in param_specs.iteritems():
                valid_file = valid_file and (get_param_str(param_name, param_val) in f)
        if valid_file:
            word = which_word(f)
            sen_type = which_sen_type(f)

            if sen_type not in sub_results:
                sub_results[sen_type] = {}
                sub_params[sen_type] = {}
                sub_time[sen_type] = {}
            if word not in sub_results[sen_type]:
                sub_results[sen_type][word] = []
                sub_params[sen_type][word] = {}
                sub_time[sen_type][word] = {}
                for param in PARAMS_TO_AGG:
                    sub_params[sen_type][word][param] = []
                sub_time[sen_type][word]['time'] = []
                sub_time[sen_type][word]['win_starts'] = []

            for param in PARAMS_TO_AGG:
                if param not in param_specs:
                    param_val = extract_param(param, f)
                    sub_params[sen_type][word][param].append(param_val)

            # print(sub_params)
            print(f)
            result = np.load(result_dir + f)
            tgm_from_preds(result['preds'], result['l_index'], result['cv_membership'], accuracy)
            # sub_results[sen_type][word].append(tgm)

            sub_time[sen_type][word]['time'] = result['time']
            sub_time[sen_type][word]['win_starts'] = result['win_starts']


if __name__ == '__main__':
    exp = 'krns2'
    mode = 'pred'
    accuracy = 'abs'
    sub = 'B'
    param_specs = {'w': 100,
                   'o': 12,
                   'pd': 'F',
                   'pr': 'F',
                   'F': 2,
                   'alg': 'LR',
                   'z': 'F',
                   'avg': 'F',
                   'ni': 2,
                   'nr': 10,
                   'rs': 1}
    agg_results(exp, mode, accuracy, sub, param_specs=param_specs)

