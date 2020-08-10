from functools import partial
from typing import Iterable, Optional, Callable, List, Tuple

from torch import nn
from torch.utils.data import Dataset

from dnn_cool.activations import CompositeActivation
from dnn_cool.datasets import FlowDataset, LeafTaskDataset
from dnn_cool.decoders import sort_declining, BinaryDecoder, TaskFlowDecoder
from dnn_cool.evaluation import EvaluationCompositeVisitor
from dnn_cool.filter import FilterCompositeVisitor, FilterVisitor
from dnn_cool.losses import TaskFlowLoss
from dnn_cool.metrics import single_result_accuracy
from dnn_cool.missing_values import positive_values, positive_values_unsqueezed
from dnn_cool.modules import SigmoidAndMSELoss, Identity, TaskFlowModule
from dnn_cool.treelib import TreeExplainer


class ITask:

    def __init__(self, name: str, inputs, available_func=None):
        self.name = name
        self.inputs = inputs
        self.available_func = available_func

    def get_name(self):
        return self.name

    def get_activation(self) -> Optional[nn.Module]:
        return None

    def get_decoder(self):
        return None

    def get_filter(self):
        return FilterVisitor(self, prefix='')

    def get_evaluator(self):
        return None

    def has_children(self):
        return False

    def get_available_func(self):
        return self.available_func

    def get_loss(self):
        raise NotImplementedError()

    def get_per_sample_loss(self):
        raise NotImplementedError()

    def torch(self):
        """
        Creates a new instance of a Pytorch module, that has to be invoked for those parts of the input, for which
        the precondition is satisfied.
        :return:
        """
        raise NotImplementedError()

    def get_inputs(self, *args, **kwargs):
        return self.inputs

    def get_labels(self, *args, **kwargs):
        raise NotImplementedError()

    def get_dataset(self, **kwargs):
        raise NotImplementedError()

    def get_metrics(self):
        return []


class Task(ITask):

    def __init__(self,
                 name: str,
                 labels,
                 loss: Callable,
                 per_sample_loss: Callable,
                 available_func: Callable = None,
                 inputs=None,
                 activation: Optional[nn.Module] = None,
                 decoder: Callable = None,
                 module: Optional[nn.Module] = Identity(),
                 metrics: List[Tuple[str, Callable]] = ()):
        super().__init__(name, inputs, available_func)
        self._activation = activation
        self._decoder = decoder
        self._loss = loss
        self._per_sample_loss = per_sample_loss
        self._module = module
        self._inputs = inputs
        self._labels = labels
        self._metrics = metrics

    def get_activation(self) -> Optional[nn.Module]:
        return self._activation

    def get_decoder(self):
        return self._decoder

    def get_loss(self):
        return self._loss

    def get_per_sample_loss(self):
        return self._per_sample_loss

    def torch(self):
        return self._module

    def get_inputs(self, *args, **kwargs):
        return self._inputs

    def get_labels(self, *args, **kwargs):
        return self._labels

    def get_dataset(self, **kwargs):
        return LeafTaskDataset(self._inputs, self._labels)

    def get_metrics(self):
        return self._metrics


class BinaryHardcodedTask(Task):

    def __init__(self,
                 name: str,
                 labels,
                 loss: Callable = None,
                 per_sample_loss: Callable = None,
                 available_func: Callable = positive_values,
                 inputs=None,
                 activation: Optional[nn.Module] = None,
                 decoder: Callable = None,
                 module: nn.Module = Identity(),
                 metrics=()):
        super().__init__(name=name,
                         labels=labels,
                         loss=loss,
                         per_sample_loss=per_sample_loss,
                         available_func=available_func,
                         inputs=inputs,
                         activation=activation,
                         decoder=decoder,
                         module=module,
                         metrics=metrics)


class BoundedRegressionTask(Task):
    """
    Represents a regression task, where the labels are normalized between 0 and 1. Examples include bounding box top
    left corners regression. Here are the defaults:
    * activation - `nn.Sigmoid()` - so that the output is in `[0, 1]`
    * loss - `SigmoidAndMSELoss` - sigmoid on the logits, then standard mean squared error loss.
    """

    def __init__(self,
                 name: str,
                 labels,
                 loss=SigmoidAndMSELoss(reduction='mean'),
                 per_sample_loss=SigmoidAndMSELoss(reduction='none'),
                 available_func: Callable = None,
                 module=Identity(),
                 activation: Optional[nn.Module] = nn.Sigmoid(),
                 decoder: Callable = None,
                 inputs=None,
                 metrics=()):
        super().__init__(name=name,
                         labels=labels,
                         loss=loss,
                         per_sample_loss=per_sample_loss,
                         available_func=available_func,
                         inputs=inputs,
                         activation=activation,
                         decoder=decoder,
                         module=module,
                         metrics=metrics)


class BinaryClassificationTask(Task):
    """
    Represents a normal binary classification task. Labels should be between 0 and 1.
    * activation - `nn.Sigmoid()`
    * loss - ``nn.BCEWithLogitsLoss()`
    """

    def __init__(self,
                 name: str,
                 labels,
                 loss=nn.BCEWithLogitsLoss(reduction='mean'),
                 per_sample_loss=nn.BCEWithLogitsLoss(reduction='none'),
                 available_func=positive_values,
                 inputs=None,
                 activation: Optional[nn.Module] = nn.Sigmoid(),
                 decoder: Callable = BinaryDecoder(),
                 module: nn.Module = Identity(),
                 metrics=(
                         ('acc_0.5', partial(single_result_accuracy, threshold=0.5, activation='Sigmoid')),
                 )):
        super().__init__(name=name,
                         labels=labels,
                         loss=loss,
                         per_sample_loss=per_sample_loss,
                         available_func=available_func,
                         inputs=inputs,
                         activation=activation,
                         decoder=decoder,
                         module=module,
                         metrics=metrics)


class ClassificationTask(Task):
    """
    Represents a classification task. Labels should be integers from 0 to N-1, where N is the number of classes
    * activation - `nn.Softmax(dim=-1)`
    * loss - `nn.CrossEntropyLoss()`
    """

    def __init__(self,
                 name: str,
                 labels,
                 loss=nn.CrossEntropyLoss(reduction='mean'),
                 per_sample_loss=nn.CrossEntropyLoss(reduction='none'),
                 available_func=positive_values_unsqueezed,
                 inputs=None,
                 activation=nn.Softmax(dim=-1),
                 decoder=sort_declining,
                 module: nn.Module = Identity(),
                 metrics=(
                         ('top_1_acc', partial(single_result_accuracy, topk=(1,), activation='Softmax')),
                         ('top_3_acc', partial(single_result_accuracy, topk=(3,), activation='Softmax')),
                 )):
        super().__init__(name=name,
                         labels=labels,
                         loss=loss,
                         per_sample_loss=per_sample_loss,
                         available_func=available_func,
                         inputs=inputs,
                         activation=activation,
                         decoder=decoder,
                         module=module,
                         metrics=metrics)


class TaskFlow(ITask):

    def __init__(self, name, tasks: Iterable[ITask], flow_func=None, inputs=None, available_func=None):
        super().__init__(name, inputs, available_func)
        self.tasks = {}
        for task in tasks:
            self.tasks[task.get_name()] = task
        if flow_func is not None:
            self._flow_func = flow_func

    def get_loss(self):
        return TaskFlowLoss(self, parent_reduction='mean', child_reduction='per_sample')

    def get_per_sample_loss(self):
        return TaskFlowLoss(self, parent_reduction='per_sample', child_reduction='per_sample')

    def torch(self):
        return TaskFlowModule(self)

    def has_children(self):
        return True

    def get_dataset(self, **kwargs) -> Dataset:
        return FlowDataset(self, **kwargs)

    def flow(self, x, out):
        raise NotImplementedError()

    def get_flow_func(self):
        if hasattr(self, '_flow_func') and self._flow_func is not None:
            return self._flow_func
        return self.__class__.flow

    def get_metrics(self):
        all_metrics = []
        for task in self.tasks.values():
            all_metrics += task.get_metrics()
        return all_metrics

    def get_treelib_explainer(self):
        return TreeExplainer(self)

    def get_labels(self, *args, **kwargs):
        all_labels = []
        for task in self.tasks.values():
            all_labels += task.get_labels()
        return all_labels

    def get_decoder(self):
        return TaskFlowDecoder(self)

    def get_activation(self) -> Optional[nn.Module]:
        return CompositeActivation(self)

    def get_evaluator(self):
        return EvaluationCompositeVisitor(self, prefix='')

    def get_filter(self):
        return FilterCompositeVisitor(self, prefix='')

    def get_all_children(self, prefix=''):
        tasks = {}
        for task_name, task in self.tasks.items():
            if task.has_children():
                tasks.update(task.get_all_children(prefix=f'{prefix}{task.get_name()}.'))
            else:
                tasks[prefix + task_name] = task
        return tasks
