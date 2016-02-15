

class MultiSignal(object):
    """MultiSignal for dynamic naming"""
    def __init__(self, signals, base_name):
        super(MultiSignal, self).__init__()
        self._signals = signals
        self._base_name = base_name
        self._set_names()

    def _set_names(self):
        self._names = ['{}_{}'.format(self._base_name, chr(i + 0x61))
                       for i in range(len(self._signals))]

    @property
    def signals(self):
        return self._signals

    @property
    def base_name(self):
        return self._base_name

    @signals.setter
    def signals(self, value):
        self._signals = value
        self._set_names()

    @base_name.setter
    def base_name(self, value):
        self._base_name = value
        self._set_names()

    def __str__(self):
        return ", ".join(self._names)

    def __get__(self, index):
        if 0 <= index < len(self._signals):
            return self._names[index]

    def __iter__(self):
        for i, name in enumerate(self._names):
            yield i, name

    def __len__(self):
        return len(self._signals)


class Templating:
    """Template for creating functions with arbitrary number of inputs/outputs"""
    def __init__(self):
        self.header = []
        self.function = []

    def __str__(self):
        return '\n'.join(self.header + self.function.split('\n'))

    def write(self, filename):
        with open(filename, 'w') as f:
            f.writelines(self.header)
            f.write('\n\n')
            f.writelines(self.function)

    @staticmethod
    def transform_signals(signals, base_name='signal'):
        return MultiSignal(signals, base_name)
