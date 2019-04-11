#! /usr/bin/env python

import numpy as np
import os
from shutil import copy2

tau = 2 * np.pi

_seed_dict = {'random': 'r'}
_node_dict = {'san': {'node_size': 16, 'mb_nx1': 32},
              'hype': {'node_size': 16, 'mb_nx1': 32, 'walltime': '24:00:00', 'script': 'run.hype.sh',
                       'exe': 'athena_hype', 'node_max': 32},
              'helios': {'node_size': 28, 'mb_nx1': 28, 'walltime': '24:00:00', 'script': 'job.sh',
                         'exe': 'athena_helios', 'node_max': 32},
              }
_walltimes = {'2:00:00': 'devel', '8:00:00': 'normal', '72:00:00': 'long'}
_res = {5: 1024, 6: 1024, 7: 2048, 8: 2048, 9: 4096, 10: 4096, 11: 4096, 12: 4096, 13: 8192, 14: 8192, 15: 8192}

_default_dir = [os.path.expanduser(i) for i in
                ['/home1/mscolema/data/bl', '~/BLayer/fft_tests', '']]
_default_dir = [i for i in _default_dir if os.path.isdir(i)][0]


def int2chr(n):
    return chr(n + 97)


def time2sec(time):
    tmp = np.array(map(int, time.split(':')))[::-1]
    return np.sum(tmp * 60**np.arange(tmp.size))


def sufix(n):
    out = []
    if n > 26:
        out.append(n // 26)
    out.append(n % 26)
    return ''.join(map(int2chr, out))


class Param(dict):
    def __init__(self, *args, **kwarg):
        defaults = dict(torb=600, seed='random', seedAmp=.01, node_max=128, x1min=None, x1max=None,
                        base_dir=_default_dir, node_type='san', mb_nx2=32, walltime='48:00:00')
        user_in = dict(*args, **kwarg)
        if 'node_type' in user_in:
            defaults['node_type'] = user_in['node_type']
        defaults.update(_node_dict[defaults['node_type']])
        defaults.update(user_in)
        super(Param, self).__init__(defaults)
        if 'queue' not in self:
            wt = time2sec(self['walltime'])
            tmp = sorted(list(_walltimes.keys()), key=time2sec)
            try:
                while wt > time2sec(tmp[0]):
                    tmp.pop(0)
            except IndexError:
                raise ValueError('No suitable queue for a walltime of {0:}.'.format(self['walltime']))
            self['queue'] = _walltimes[tmp[0]]
        self._set('tf0', 1.)
        self['tf0'] *= tau
        if 'torb' in self and 'tlim' not in self:
            self['tlim'] = self['torb'] * tau
        if 'nr' in self and 'nx1' not in self:
            self['nx1'] = self['nr']
        if 'nphi' in self and 'nx2' not in self:
            self['nx2'] = self['nphi']
        if 'rmin' in self and self['x1min'] is None:
            self['x1min'] = self['rmin']
        if 'rmax' in self and self['x1max'] is None:
            self['x1max'] = self['rmax']
        self._set('contrast', 1e7)
        if self['x1min'] is None:
            self['x1min'] = 1. / (1. + self['mach']**-2 * np.log(self['contrast']))
        if self['x1max'] is None:
            self['x1max'] = 4
        self['_seed'] = _seed_dict.get(self['seed'], self['seed'])
        self._set('cs', 1. / self['mach'])
        if 'nx1' not in self and 'nx2' not in self:
            if self.get('lr'):
                self._set('res_str', 'LR')
            elif self.get('hr'):
                self._set('res_str', 'HR')
            else:
                self._set('res_str', 'FR')
        if 'nx1' not in self:
            if self.get('lr') and self.get('hr'):
                raise ValueError('"lr" and "hr" are both specified.')
            if self.get('lr'):
                self['nx1'] = _res[self['mach']] // 2
            elif self.get('hr'):
                self['nx1'] = _res[self['mach']] * 2
            else:
                self['nx1'] = _res[self['mach']]
            if self['node_size'] == 28:
                self['nx1'] = (self['nx1'] // 8) * 7
        if 'nx2' not in self:
            if self.get('lr') and self.get('hr'):
                raise ValueError('"lr" and "hr" are both specified.')
            if self.get('lr'):
                self['nx2'] = _res[self['mach']] // 2
            elif self.get('hr'):
                self['nx2'] = _res[self['mach']] * 2
            else:
                self['nx2'] = _res[self['mach']]
        if 'res_str' not in self:
            self['res_str'] = '{nx2:d}.{nx1:d}'.format(**self)
        self._set('x1rat', (float(self['x1max']) / self['x1min']) ** (1. / self['nx1']))
        self['nblocks'] = (self['nx1'] // self['mb_nx1']) * (self['nx2'] // self['mb_nx2'])
        if 'node_num' not in self:
            if self['node_max']:
                self._set('core_num', min(self['node_max'] * self['node_size'], self['nblocks']))
            else:
                self._set('core_num',  self['nblocks'])
            self['node_num'] = self['core_num'] // self['node_size']
        else:
            self['core_num'] = self['node_num'] * self['node_size']
        if 'stop_time' not in self:
            tmp = list(map(int, self['walltime'].split(':')))
            tmp[0] -= 1
            tmp[1] = 59
            self['stop_time'] = ':'.join(['%02d' % i for i in tmp])
        # Do these last in init
        self['base_dir'] = os.path.expanduser(self['base_dir'])
        if 'name' not in self:
            self._gen_name()
        self._set('path', os.path.join(self['base_dir'], self['name']))
        self['path'] = os.path.expanduser(self['path'])

    def _set(self, key, value=None):
        if key not in self:
            self[key] = value

    def _gen_name(self):
        tmp = 'M{mach:02d}.{res_str:}.{_seed:}.'.format(**self)
        n = 0
        while os.path.isdir(os.path.join(self['base_dir'], tmp + int2chr(n))):
            n += 1
        self['name'] = tmp + int2chr(n)

    def mkdir(self):
        os.mkdir(self['path'])

    def _reproduce(self, infile, outfile):
        with open(infile, 'r') as fin:
            text = fin.read()
        text = text.format(**self)
        with open(outfile, 'w') as fout:
            fout.write(text)
        return None

    def athinput(self, outfile=None, infile=None):
        if infile is None:
            infile = os.path.join(os.path.split(__file__)[0], 'athinput.bl')
        if outfile is None:
            outfile = os.path.join(self['path'], os.path.split(infile)[-1])
        print(self['name'])
        self._reproduce(infile, outfile)

    def script(self, outfile=None, infile=None):
        if infile is None:
            infile = os.path.join(os.path.split(__file__)[0], self.get('script', 'run.sh'))
        if outfile is None:
            outfile = os.path.join(self['path'], os.path.split(infile)[-1])
        self._reproduce(infile, outfile)

    def cp_exe(self, dst=None, src=None):
        if src is None:
            src = os.path.join(os.path.split(__file__)[0], self.get('exe', 'athena'))
            if not os.path.isfile(src):
                src = os.path.split(os.path.split(os.path.abspath(__file__))[0])[0]
                src = os.path.join(src, 'bin', 'athena')
        if dst is None:
            dst = os.path.join(self['path'], 'athena')
        elif os.path.isdir(dst):
            dst = os.path.join(dst, 'athena')
        copy2(src, dst)

    def mksim(self, cd=None):
        self.mkdir()
        self.athinput()
        self.script()
        self.cp_exe()
        if cd is None:
            cd = self.get('cd')
        if cd:
            os.chdir(self['path'])


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Set up a BL simulation directory.')
    parser.add_argument('-m', '--mach', nargs='?', type=float, help='Mach number')
    parser.add_argument('--nr', nargs='?', type=int, help='Radial resolution')
    parser.add_argument('--nphi', nargs='?', type=int, help='Azimuthal resolution')
    parser.add_argument('--walltime', nargs='?', type=str, help='Simulation walltime')
    parser.add_argument('-s', '--seed', nargs='?', type=str, help='Seed type [m#, mix, random]')
    parser.add_argument('--seedAmp', nargs='?', type=float, help='Seed perturbation amplitude')
    parser.add_argument('--cd', action='store_true', help='cd to simulation directory')
    parser.add_argument('--base_dir', nargs='?', type=str,
                        help='Choose simulation base directory [{0:}]'.format(_default_dir))
    parser.add_argument('--rmin', nargs='?', type=float, help='')
    parser.add_argument('--rmax', nargs='?', type=float, help='')
    parser.add_argument('--node_max', nargs='?', type=int, help='Max number of nodes to use')
    parser.add_argument('--node_type', nargs='?', type=str, help='Type of nodes to use')
    parser.add_argument('--torb', nargs='?', type=float, help='Number of inner orbits to run')
    parser.add_argument('-lr', action='store_true', help='low resolution')
    parser.add_argument('-hr', action='store_true', help='high resolution')
    # parser.add_argument('--tf0', nargs='?', type=float, help='File output time unit')

    args = vars(parser.parse_args())
    opt = {i: args[i] for i in args if args[i] is not None}
    if opt['mach'] == int(opt['mach']):
        opt['mach'] = int(opt['mach'])

    p = Param(**opt)
    p.mksim()
