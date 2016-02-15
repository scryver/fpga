from fpga.utils import create_signals
from fpga.templates.template import Templating


class MuxTemplate(Templating):
    multimux = """
def mux({mux_inputs}, sel, dout):

    @always_comb
    def logic():
        {elif_template}
        else: dout.next = 0

    return logic
""".format

    def __init__(self, input_signals):
        super().__init__()
        self.header.append("from myhdl import always_comb")
        in_sig = self.transform_signals(input_signals, 'in')
        self.function = self.multimux(mux_inputs=in_sig,
                                      elif_template=self.join_elif(in_sig))

    def join_elif(self, names):
        elif_template = 'if sel == {sel}: dout.next = {val}'.format
        return '\n        el'.join((elif_template(sel=i + 1, val=name)
                                    for i, name in names))


inputs = create_signals(6, 21, signed=True, delay=None)
muxer = MuxTemplate(inputs)
muxer.write('luktdit.py')
