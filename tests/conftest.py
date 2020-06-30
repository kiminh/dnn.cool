import pytest
from torch import nn

from dnn_cool.modules import Identity
from dnn_cool.task_flow import BinaryClassificationTask, TaskFlow, BinaryHardcodedTask, LocalizationTask, \
    ClassificationTask, RegressionTask, NestedClassificationTask


@pytest.fixture(scope='package')
def carsbg():
    class IsCarModule(nn.Module):

        def __init__(self, fc):
            super().__init__()
            self.fc = fc

        def forward(self, features, sliced):
            res = self.fc(features)
            res[sliced.decoded] = 1e3
            return res

    class IsCarTask(BinaryClassificationTask):

        def torch(self) -> nn.Module:
            return IsCarModule(super().torch())

    class CarsBgNetFlow(TaskFlow):

        def __init__(self):
            base_options = {
                'in_features': 2560,
                'bias': True
            }
            super().__init__(
                name='carsbg_flow',
                tasks=[
                    BinaryHardcodedTask(name='sliced'),
                    LocalizationTask(name='car_localization', module_options=base_options),
                    LocalizationTask(name='license_plate_localization', module_options=base_options),
                    IsCarTask(name='is_car', module_options=base_options),
                    BinaryClassificationTask(name='has_license_plate', module_options=base_options),
                    ClassificationTask(name='brand', module_options={
                        'in_features': 2560,
                        'out_features': 4,
                        'bias': True
                    }),
                    ClassificationTask(name='color', module_options={
                        'in_features': 2560,
                        'out_features': 26,
                        'bias': True
                    }),
                    RegressionTask(name='year', module_options={
                        'in_features': 2560,
                        'out_features': 1,
                        'bias': True
                    }, activation_func=nn.Sigmoid()),
                    NestedClassificationTask(name='model', top_k=5, module_options={
                        'in_features': 2560,
                        'out_features_nested': [9, 15, 2, 12],
                        'bias': True
                    })
                ])

        def flow(self, x, out):
            out += self.sliced(x.sliced)
            out += self.car_localization(x.car) | (~out.sliced)

            out += self.is_car(x.car, out.sliced)

            out += self.brand(x.common) | out.is_car
            out += self.color(x.common) | out.is_car
            out += self.year(x.common) | out.is_car

            out += self.model(x.common, out.brand) | out.is_car

            out += self.has_license_plate(x.lp) | out.is_car
            out += self.license_plate_localization(x.lp) | (out.has_license_plate & out.is_car)

            return out

    carsbg = CarsBgNetFlow()
    return carsbg


@pytest.fixture(scope='package')
def yolo_anchor():

    class YoloAnchorFlow(TaskFlow):

        def __init__(self):
            super().__init__(
                name='yolo_flow',
                tasks=[
                    BinaryClassificationTask(name='has_object', module_options={
                        'in_features': 2560,
                        'bias': True
                    }),
                    RegressionTask(name='xy', module_options={
                        'in_features': 2560,
                        'out_features': 2,
                        'bias': True
                    }, activation_func=nn.Sigmoid()),
                    RegressionTask(name='wh', module_options={
                        'in_features': 2560,
                        'out_features': 2,
                        'bias': True
                    }, activation_func=Identity()),
                    ClassificationTask(name='object_class', module_options={
                        'in_features': 2560,
                        'out_features': 10,
                        'bias': True
                    })
                ])

        def flow(self, x, out):
            out += self.has_object(x.features)
            out += self.xy(x.features) | out.has_object
            out += self.wh(x.features) | out.has_object
            out += self.object_class(x.features) | out.has_object
            return out

    carsbg = YoloAnchorFlow()
    return carsbg


@pytest.fixture(scope='package')
def nested_carsbg(carsbg):
    module_options = {
        'in_features': 2560,
        'bias': True
    }
    camera_blocked = BinaryClassificationTask(name='camera_blocked', module_options=module_options)

    class CameraBlockedCarsBgFlow(TaskFlow):

        def __init__(self):
            super().__init__('camera_blocked_carsbg_flow', [camera_blocked, carsbg])

        def flow(self, x, out):
            out += self.camera_blocked(x.common)
            out += self.carsbg_flow(x) | out.camera_blocked
            return out

    return CameraBlockedCarsBgFlow()


@pytest.fixture(scope='package')
def simple_linear_pair():

    class SimpleConditionalFlow(TaskFlow):

        def __init__(self, tasks):
            super().__init__(name='simple_conditional_flow', tasks=tasks)

        def flow(self, x, out):
            out += self.is_positive(x.features)
            out += self.positive_func(x.features) | out.is_positive
            out += self.negative_func(x.features) | (~out.is_positive)
            return out

    is_positive = BinaryClassificationTask(name='is_positive', module_options={'in_features': 128})
    positive_func = RegressionTask(name='positive_func', module_options={'in_features': 128},
                                   activation_func=Identity())
    negative_func = RegressionTask(name='negative_func', module_options={'in_features': 128},
                                   activation_func=Identity())
    tasks = [is_positive, positive_func, negative_func]
    simple_flow = SimpleConditionalFlow(tasks)

    class SimpleMultiTaskModule(nn.Module):

        def __init__(self):
            super().__init__()
            n_features = 128
            self.seq = nn.Sequential(
                nn.Linear(1, 64, bias=True),
                nn.ReLU(inplace=True),
                nn.Linear(64, n_features, bias=True),
                nn.ReLU(inplace=True),
            )
            self.simple_flow_module = simple_flow.torch()

        def forward(self, x):
            x['features'] = self.seq(x['features'])
            return self.simple_flow_module(x)

    return SimpleMultiTaskModule(), simple_flow


@pytest.fixture(scope='package')
def simple_nesting_linear_pair():

    class PositiveFlow(TaskFlow):

        def __init__(self, tasks):
            super().__init__(name='positive_flow', tasks=tasks)

        def flow(self, x, out):
            out += self.positive_func(x.features)
            return out

    class NegativeFlow(TaskFlow):

        def __init__(self, tasks):
            super().__init__(name='negative_flow', tasks=tasks)

        def flow(self, x, out):
            out += self.negative_func(x.features)
            return out

    class SimpleConditionalFlow(TaskFlow):

        def __init__(self, tasks):
            super().__init__(name='simple_conditional_flow', tasks=tasks)

        def flow(self, x, out):
            out += self.is_positive(x.features)
            out += self.positive_flow(x) | out.is_positive
            out += self.negative_flow(x) | (~out.is_positive)
            return out

    is_positive = BinaryClassificationTask(name='is_positive', module_options={'in_features': 128})
    positive_func = RegressionTask(name='positive_func', module_options={'in_features': 128},
                                   activation_func=Identity())
    negative_func = RegressionTask(name='negative_func', module_options={'in_features': 128},
                                   activation_func=Identity())
    positive_flow = PositiveFlow(tasks=[positive_func])
    negative_flow = NegativeFlow(tasks=[negative_func])
    tasks = [is_positive, positive_flow, negative_flow]
    simple_flow = SimpleConditionalFlow(tasks)

    class SimpleMultiTaskModule(nn.Module):

        def __init__(self):
            super().__init__()
            n_features = 128
            self.seq = nn.Sequential(
                nn.Linear(1, 64, bias=True),
                nn.ReLU(inplace=True),
                nn.Linear(64, n_features, bias=True),
                nn.ReLU(inplace=True),
            )
            self.simple_flow_module = simple_flow.torch()

        def forward(self, x):
            x['features'] = self.seq(x['features'])
            return self.simple_flow_module(x)

    return SimpleMultiTaskModule(), simple_flow
