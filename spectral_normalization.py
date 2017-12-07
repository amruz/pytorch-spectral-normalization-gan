import torch
from torch.optim.optimizer import Optimizer, required

from torch.autograd import Variable
import torch.nn.functional as F
from torch import nn


class SpectralNormOptimizer(Optimizer):

	def __init__(self, params, lr=required):
		defaults = dict(lr=lr)

		super(SpectralNormOptimizer, self).__init__(params, defaults)

	def step(self, closure=None):
		loss = None
		if closure is not None:
			loss = closure()

		for group in self.param_groups:

			for p in group['params']:
				if p.grad is None:
					continue

				d_p = p.grad.data
				p.data.add_(-group['lr'], d_p)

		return loss


#approximates the spectral norm (maximum singular value) of W
#uses power iteration method
def spectral_norm(W, u=None, power_iterations=1):

	#filter height and width

	height = W.data.shape[0]
	width = W.data.shape[1]
	if len(W.data.shape) > 2:
		width = W.data.shape[1] * W.data.shape[2] * W.data.shape[3]
	
	u_n = u
	for i in range(power_iterations):
		v_n = F.normalize(torch.mv(torch.t(W.view(height,-1).data), u_n), p=2, dim=0)
		u_n = F.normalize(torch.mv(W.view(height,-1).data, v_n), p=2, dim=0)

	prod = torch.mv(W.view(height,-1).data, v_n)
	singular_value = torch.dot(u_n, prod)
	return singular_value, u_n, v_n

class SpectralNorm(nn.Module):
    def __init__(self, module):
        super(SpectralNorm, self).__init__()
        self.module = module
        self.u = Variable(self.module.weight.data.new((self.module.weight.data.shape[0]))).cuda().data.normal_(0,1)


    def _setweights(self):
        singular_value, u, _ = spectral_norm(self.module.weight, self.u)
        self.module.weight.data = self.module.weight.data / singular_value
        self.u = u

    def forward(self, *args):
        self._setweights()
        return self.module.forward(*args)