# dnn.cool

Some dumb stuff I am playing with.

DOING:

- [ ] Create a helper class for creating tasks (by trying to guess task type) - e.g ProjectHelper

TODO:

- [x] Generate a `nn.Module` with `train` mode, which works correctly.
- [x] Generate a `nn.Module` with `eval` mode, which works correctly.
- [ ] Per-task evaluation information, given that precondition is working correctly.
- [ ] Overall evaluation information
- [ ] Per-task result interpretation
- [ ] Overall interpretation
- [x] Per-task loss function `nn.Module`s
- [x] Overall loss function as `nn.Module`
- [x] Per-task metrics
- [x] Overall metrics
- [x] Predictions per task
- [ ] Freeze-all but task feature (including Batch Norm) - may include parameter group
- [ ] Set learning rate per task feature
- [x] Callbacks per task (for metrics, loss function, additional metrics, samples, etc.)
- [ ] Interpretation callback
- [ ] Sample decoded results per task
- [ ] Handles missing labels correctly.
- [x] Concept of per-task activation/decoding.
- [x] Overall activation/decoding (topological sorting, etc.).
- [ ] Automatic per-task or overall hyperparameter tuning.
- [ ] Composite flows (e.g YOLO inside a classifier, etc.)
- [ ] UI splitting helper
- [ ] ONNX converter (if possible) - with static analysis.
- [ ] Test training a model with synthetic dataset.
- [x] Help with logic when creating `nn.Dataset`.
- [ ] Treelib explanation
- [ ] Grad-CAM per branch
- [x] Can debug the flow in any mode
- [ ] Cleaner representations for results
- [ ] Work on error messages
- [ ] Predict only for those, for which precondition is correct.
- [ ] Allow custom entries in the FlowDict
- [ ] Add to latex option (automatically generate loss functions in latex)
- [x] Think of way to handle properly the or operator.
- [ ] Implement YOLO for example
- [ ] Add possibility to add weights based on masks
- [x] Correct handling when multiple precondition masks are present
- [ ] Correct operations override for magic methods
- [ ] Improve variable names
- [ ] Add option to skip flatten (for inference it's actually better to keep it, but for loaders it has to be flattened)
- [ ] Customization - add the possibility to pass not only the logits, but other keys as well (maybe include them by default?)
- [ ] Add option for readable output
- [ ] Add a lot of predefined tasks and flows
- [ ] Rethink reduction and variable names
- [ ] Compute only when precondition is True (will require precomputing)
- [ ] Pass around kwargs for flexibility
- [x] Nested loss functions check and test
- [ ] Support multilabel classification problem
- [x] Think how suitable it would be to use scoping
- [x] Fix bug with the results seem weird
- [x] Optimize inputs (so that it is not read multiple times)
- [x] Make good tests for cascading preconditions (especially for datasets).
- [ ] Make sure immutability of objects is preserved
- [x] Performance issues
- [ ] Documentation
- [ ] Think of useful methods
- [ ] Think of a better way to organize labels
- [ ] Add the possibility to predict given the precondition is true (very useful for evaluation)
- [ ] Test with very weird cases
- [ ] Receptive field slicing
- [ ] Proper handling of multimetrics (not adding them one by one).
- [x] Debug why metrics are wrong
- [x] Refactor decorators
- [ ] Use train/test split in tests
- [ ] Augmentations helper
- [ ] Incremental re-run
- [ ] Support for classification special case handling.
- [ ] Add and implement nice default metrics for different tasks.
- [ ] Think of default values for different tasks.
- [ ] Add per sample activation
- [ ] Spend time thinking about user-friendliness of each class (think about what mistakes would people do?).
- [ ] Good tests about possible gt leak
- [ ] Implement tracing for static analysis (later)
- [ ] Create convincing synthetic dataset
- [ ] Create real dataset by pseudo labeling
- [ ] Rethink user-friendliness API
- [ ] Revisit type hints
- [ ] Auto guess task from column