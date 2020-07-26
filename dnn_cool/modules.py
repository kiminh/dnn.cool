import torch

from typing import Dict, Union, Optional

from dataclasses import dataclass, field
from torch import nn


class SigmoidAndMSELoss(nn.Module):

    def __init__(self, reduction):
        super().__init__()
        self.sigmoid = nn.Sigmoid()
        self.mse = nn.MSELoss(reduction=reduction)

    def forward(self, output, target):
        activated_output = self.sigmoid(output)
        return self.mse(activated_output, target)


class Identity(nn.Module):
    def __init__(self, *args, **kwargs):
        super().__init__()

    def forward(self, x):
        return x


# TODO: is there a way to vectorize this in case all counts are different?
class NestedFC(nn.Module):

    def __init__(self, in_features, out_features_nested, bias, top_k):
        super().__init__()
        fcs = []
        for i, out_features in enumerate(out_features_nested):
            fcs.append(nn.Linear(in_features, out_features, bias))
        self.fcs = nn.ModuleList(fcs)
        self.top_k = top_k

    def forward(self, features, parent_flow_dict):
        """
        features and parent_indices must have the same length. Iterates over parent indices, and records predictions
        for every pair (N, P), where N is a batch number and P is a parent index. returns list of lists.
        :param features:
        :param parent_indices: FlowDict which holds the results
        :return: list of lists of lists, where every element is the prediction of the respective module. The first
        len is equal to the batch size, the second len is equal to the top_k and the third len is equal to the respective
        number of classes for the child FC.
        """
        n = len(features)
        parent_indices = parent_flow_dict.decoded[:, :self.top_k]
        res = []
        for i in range(n):
            res_for_parent = []
            for parent_index in parent_indices[i]:
                res_for_parent.append(self.fcs[parent_index](features[i:i + 1]))
            res.append(res_for_parent)
        return res


def find_arg_with_gt(args, is_kwargs):
    new_args = {} if is_kwargs else []
    gt = None
    for arg in args:
        if is_kwargs:
            arg = args[arg]
        try:
            gt = arg['gt']
            new_args.append(arg['value'])
        except:
            new_args.append(arg)
    return gt, new_args


def select_gt(a_gt, k_gt):
    if a_gt is None and k_gt is None:
        return {}

    if a_gt is None:
        return k_gt

    return a_gt


def find_gt_and_process_args_when_training(*args, **kwargs):
    a_gt, args = find_arg_with_gt(args, is_kwargs=False)
    k_gt, kwargs = find_arg_with_gt(kwargs, is_kwargs=True)
    return args, kwargs, select_gt(a_gt, k_gt)


class ModuleDecorator(nn.Module):

    def __init__(self, task, prefix):
        super().__init__()
        self.prefix = prefix
        self.task_name = task.get_name()
        self.module = task.torch()
        self.activation = task.get_activation()
        self.decoder = task.get_decoder()

    def forward(self, *args, **kwargs):
        if self.training:
            args, kwargs, gt = find_gt_and_process_args_when_training(*args, **kwargs)
            decoded_logits = gt.get(self.task_name, None)
        else:
            decoded_logits = None

        logits = self.module(*args, **kwargs)
        activated_logits = self.activation(logits) if self.activation is not None else logits

        if decoded_logits is None:
            decoded_logits = self.decoder(activated_logits) if self.decoder is not None else activated_logits
        key = self.prefix + self.task_name
        return LeafModuleOutput(key, logits, activated_logits, decoded_logits)


class Precondition:

    def to_mask(self, data):
        """
        Returns a boolean tensor that can be used as a precondition
        :param data: can come either from ground truth (during training), or from decoded predictions (when deployed)
        :return:
        """
        raise NotImplementedError()

    def __invert__(self):
        return NegatedPrecondition(self)


@dataclass()
class NegatedPrecondition(Precondition):
    precondition: Precondition

    def to_mask(self, data):
        mask = self.precondition.to_mask(data)
        return ~mask


@dataclass
class LeafPrecondition(Precondition):
    path: str

    def to_mask(self, data):
        return data[self.path]


@dataclass()
class NestedPrecondition(Precondition):
    path: str
    parent: Precondition

    def to_mask(self, data):
        mask = self.parent.to_mask(data)
        precondition = data[self.path]
        mask[~precondition] = False
        return mask


@dataclass
class LeafModuleOutput:
    path: str
    logits: torch.Tensor
    activated: torch.Tensor
    decoded: torch.Tensor
    precondition: Precondition = None

    def add_to_composite(self, composite_module_output):
        composite_module_output.logits[self.path] = self.logits
        composite_module_output.activated[self.path] = self.activated
        composite_module_output.decoded[self.path] = self.decoded
        composite_module_output.preconditions[self.path] = self.precondition

    def __or__(self, precondition: Precondition):
        """
        Note: this has the meaning of a a precondition, not boolean or. Use the method `or_else` instead.
        :param other: precondition tensor
        :return: self
        """
        self.precondition = precondition
        return self


@dataclass
class CompositeModuleOutput:
    training: bool
    gt: Dict[str, torch.Tensor]
    prefix: str
    path: str = ''
    logits: Dict[str, torch.Tensor] = field(default_factory=lambda: {})
    activated: Dict[str, torch.Tensor] = field(default_factory=lambda: {})
    decoded: Dict[str, torch.Tensor] = field(default_factory=lambda: {})
    preconditions: Dict[str, Precondition] = field(default_factory=lambda: {})

    def add_to_composite(self, other):
        for key, value in self.logits.items():
            assert key not in other.logits, f'The key {key} has been added twice in the same workflow!.'
            other.logits[key] = value
        for key, value in self.activated.items():
            assert key not in other.activated, f'The key {key} has been added twice in the same workflow!.'
            other.activated[key] = value
        for key, value in self.decoded.items():
            assert key not in other.decoded, f'The key {key} has been added twice in the same workflow!.'
            other.decoded[key] = value
        for key, value in self.preconditions.items():
            assert key not in other.preconditions, f'The key {key} has been added twice in the same workflow!.'
            other.preconditions[key] = value

    def __iadd__(self, other):
        other.add_to_composite(self)
        return self

    def __getattr__(self, item):
        full_path = self.prefix + item
        parent_precondition = self.preconditions.get(full_path)
        if parent_precondition is None:
            return LeafPrecondition(path=full_path)
        return NestedPrecondition(path=full_path, parent=parent_precondition)

    def __or__(self, precondition: Precondition):
        """
        Note: this has the meaning of a a precondition, not boolean or. Use the method `or_else` instead.
        :param other: precondition tensor
        :return: self
        """
        for key, value in self.preconditions.items():
            current_precondition = self.preconditions.get(key)
            if current_precondition is None:
                self.preconditions[key] = precondition
            else:
                self.preconditions[key] &= precondition
        return self

    def reduce(self):
        if len(self.prefix) == 0:
            res = self.logits
            for key, value in self.preconditions.items():
                if value is not None:
                    res[f'precondition|{key}'] = value.to_mask(self.gt)
            return res
        return self


@dataclass
class FeaturesDict:
    data: Dict

    def __init__(self, data):
        self.data = data

    def __getattr__(self, item):
        return self.data[item]


class TaskFlowModule(nn.Module):

    def __init__(self, task_flow, prefix=''):
        super().__init__()
        self._task_flow = task_flow
        # Save a reference to the flow function of the original class
        # We wi.ll then call it by replacing the self, this way effectively running
        # it with this class. And this class stores Pytorch modules as class attributes
        self.flow = task_flow.get_flow_func()
        self.prefix = prefix

        for key, task in task_flow.tasks.items():
            if not task.has_children():
                instance = ModuleDecorator(task, prefix)
            else:
                instance = TaskFlowModule(task, prefix=f'{prefix}{task.get_name()}.')
            setattr(self, key, instance)

    def forward(self, x):
        if isinstance(x, FeaturesDict):
            x = x.data

        out = CompositeModuleOutput(training=self.training, gt=x.get('gt'), prefix=self.prefix)
        composite_module_output = self.flow(self, FeaturesDict(x), out)
        return composite_module_output.reduce()
