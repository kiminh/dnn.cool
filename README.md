# dnn.cool

Task:


- [x] Generate a `nn.Module` with `train` mode, which works correctly.
- [x] Generate a `nn.Module` with `eval` mode, which works correctly.
- [ ] Per-task evaluation information, given that precondition is working correctly.
- [ ] Overall evaluation information
- [ ] Per-task result interpretation
- [ ] Overall interpretation
- [ ] Per-task loss function `nn.Module`s
- [x] Overall loss function as `nn.Module`
- [ ] Per-task metrics
- [ ] Overall metrics
- [ ] Predictions per task
- [ ] Freeze-all but task feature (including Batch Norm) - may include parameter group
- [ ] Set learning rate per task feature
- [ ] Callbacks per task (for metrics, loss function, additional metrics, samples, etc.)
- [ ] Sample decoded results per task
- [ ] Handles missing labels correctly.
- [x] Concept of per-task activation/decoding.
- [x] Overall activation/decoding (topological sorting, etc.).
- [ ] Automatic per-task or overall hyperparameter tuning.
- [ ] Composite flows (e.g YOLO inside a classifier, etc.)
- [ ] UI splitting helper
- [ ] ONNX converter (if possible) - with static analysis.
- [ ] Test training a model with synthetic dataset.
- [ ] Help with logic when creating `nn.Dataset`.
- [ ] Treelib explanation
- [ ] Grad-CAM per branch
- [ ] Can debug the flow in any mode
- [ ] Cleaner representations for results
- [ ] Work on error messages
- [ ] Predict only for those, for which precondition is correct.
- [ ] Allow custom entries in the FlowDict
- [ ] Add to latex option (automatically generate loss functions in latex)
- [ ] Think of way to handle properly the or operator.
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
- [ ] Compute only when precondition is True (will requires precomputing)
- [ ] Pass around kwargs for flexibility