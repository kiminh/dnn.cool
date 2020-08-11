import tempfile
from collections import OrderedDict

from catalyst.dl import SupervisedRunner
from torch import optim
from torch.utils.data import DataLoader

from dnn_cool.synthetic_dataset import synthenic_dataset_preparation
from dnn_cool.task_flow import TaskFlow
from dnn_cool.utils import torch_split_dataset
from tests.test_very_simple_train import print_any_prediction


def test_passenger_example(interior_car_task):
    model, task_flow = interior_car_task

    dataset = task_flow.get_dataset()

    train_dataset, val_dataset = torch_split_dataset(dataset, random_state=42)
    train_loader = DataLoader(train_dataset, batch_size=64, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=64, shuffle=False)
    nested_loaders = OrderedDict({
        'train': train_loader,
        'valid': val_loader
    })

    print(model)

    runner = SupervisedRunner()
    criterion = task_flow.get_loss()
    callbacks = criterion.catalyst_callbacks()

    with tempfile.TemporaryDirectory() as tmp_dir:
        print(tmp_dir)
        runner.train(
            model=model,
            criterion=criterion,
            optimizer=optim.Adam(model.parameters(), lr=1e-3),
            loaders=nested_loaders,
            callbacks=callbacks,
            logdir=tmp_dir,
            num_epochs=40,
        )

    print_any_prediction(criterion, model, nested_loaders, runner)


def test_synthetic_dataset():
    model, nested_loaders, datasets, project = synthenic_dataset_preparation()
    runner = project.runner(model=model, runner_name='security_logs')
    flow: TaskFlow = project.get_full_flow()
    criterion = flow.get_loss()
    callbacks = criterion.catalyst_callbacks()

    runner.train(
        model=model,
        criterion=criterion,
        optimizer=optim.Adam(model.parameters(), lr=1e-4),
        loaders=nested_loaders,
        callbacks=callbacks,
        num_epochs=10,
    )

    print_any_prediction(criterion, model, nested_loaders, runner)


def test_synthetic_dataset_default_runner():
    model, nested_loaders, datasets, project = synthenic_dataset_preparation()
    runner = project.runner(model=model, runner_name='default_experiment')
    flow: TaskFlow = project.get_full_flow()
    criterion = flow.get_loss()

    runner.train(num_epochs=10)

    early_stop_callback = runner.default_callbacks[-1]
    assert early_stop_callback.best_score >= 0, 'Negative loss function!'
    print_any_prediction(criterion, model, nested_loaders, runner)