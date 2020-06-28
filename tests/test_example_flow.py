from dnn_cool.task_flow import TaskFlow, NestedResult, BinaryClassificationTask, ClassificationTask, \
    BinaryHardcodedTask, LocalizationTask, NestedClassificationTask, RegressionTask


def test_example_flow():

    class CarsBgNetFlow(TaskFlow):

        def __init__(self):
            super().__init__(
                name='carsbg_flow',
                tasks=[
                    BinaryHardcodedTask(name='sliced'),
                    LocalizationTask(name='car_localization', module_options={
                        'in_features': 2560,
                        'bias': True
                    }),
                    LocalizationTask(name='license_plate_localization', module_options={
                        'in_features': 2560,
                        'bias': True
                    }),
                    BinaryClassificationTask(name='is_car', module_options={
                        'in_features': 2560,
                        'bias': True
                    }),
                    BinaryClassificationTask(name='has_license_plate', module_options={
                        'in_features': 2560,
                        'bias': True
                    }),
                    ClassificationTask(name='brand', module_options={
                        'in_features': 2560,
                        'out_features': 80,
                        'bias': True
                    }),
                    ClassificationTask(name='color', module_options={
                        'in_features': 2560,
                        'out_features': 26,
                        'bias': True
                    }),
                    RegressionTask(name='year'),
                    NestedClassificationTask(name='model', top_k=5)
                ])

        def flow(self, x: NestedResult) -> NestedResult:
            out = NestedResult(self)
            out += self.sliced(x)
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
    task_input = NestedResult(carsbg)
    task_input.res['car'] = 2560
    task_input.res['common'] = 2560
    task_input.res['lp'] = 2560
    r = carsbg.flow(task_input)

    print('Final res')
    print(r)

    print(r.is_car.torch())
    print(r.has_license_plate.torch())
    print(r.brand.torch())
    print(r.color.torch())
    print(r.sliced.torch())
    print(r.car_localization.torch())
    print(r.license_plate_localization.torch())

