import torch.nn as nn
import torch.nn.functional as F
import math
import torch
import torch.optim as optim
from torch.nn.parameter import Parameter
from torch.nn.modules.module import Module
from itertools import product
import numpy as np

class PGE(nn.Module):

    def __init__(self, nfeat, nnodes, nhid=128, nlayers=3, device=None, args=None):
        super(PGE, self).__init__()
        self.layers = nn.ModuleList([])
        self.layers.append(nn.Linear(nfeat*2, nhid))
        self.bns = torch.nn.ModuleList()
        self.bns.append(nn.BatchNorm1d(nhid))
        for i in range(nlayers-2):
            self.layers.append(nn.Linear(nhid, nhid))
            self.bns.append(nn.BatchNorm1d(nhid))
        self.layers.append(nn.Linear(nhid, 1))

        edge_index = np.array(list(product(range(nnodes), range(nnodes))))
        self.edge_index = edge_index.T
        self.nnodes = nnodes
        self.device = device
        self.reset_parameters()
        self.cnt = 0
        self.args = args
        self.nnodes = nnodes

    def forward(self, x, inference=False):
        edge_index = self.edge_index
        edge_embed = torch.cat([x[edge_index[0]],x[edge_index[1]]], axis=1)
        for ix, layer in enumerate(self.layers):
            edge_embed = layer(edge_embed)
            if ix != len(self.layers) - 1:
                edge_embed = self.bns[ix](edge_embed)
                edge_embed = F.relu(edge_embed)
        adj = edge_embed.reshape(self.nnodes, self.nnodes)
        adj = (adj + adj.T)/2
        adj = torch.sigmoid(adj)
        adj = adj - torch.diag(torch.diag(adj, 0))
        return adj

    @torch.no_grad()
    def inference(self, x):
        self.eval()
        adj_syn = self.forward(x, inference=True)
        return adj_syn

    def reset_parameters(self):
        def weight_reset(m):
            if isinstance(m, nn.Linear):
                m.reset_parameters()
            if isinstance(m, nn.BatchNorm1d):
                m.reset_parameters()
        self.apply(weight_reset)
