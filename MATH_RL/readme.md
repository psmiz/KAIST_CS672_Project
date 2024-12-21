## Augmentation method

We follow the data format of the Alphabetization task in 
[RL4F (ACL 2023)](https://aclanthology.org/2023.acl-long.427/).

For supervised training, each original solution is modified into 
2 wrong solutions with corresponding critiques by `GPT-4o-mini-2024-07-18`. 
The original solution is also included with the critique "The solution is correct."
The results are in the json format
```
{
    "text": "{question} ||| {solution}",
    "summary": {critique},
    "level": {level},
    "type": {type},
    "id": {type}
}
```
For convenience, the level, type, and id of the original question is included for 
easy retrieval and analysis.

For PPO training, each original solution is modified into 2 wrong solutions by
`GPT-4o-mini-2024-07-18`. The results are in the json format
```
{
    "text": "{question} ||| {solution}",
    "summary": {correct solution},
    "level": {level},
    "type": {type},
    "id": {type}
}
```


## SUP + PPO training

tasks: algebra, intermediate_algebra, prealgebra
subsets: dev, test, train
modes: ppo_sampled, sup
number of samples:
```
algebra/train_sup: 1779 samples
algebra/train_ppo_sampled: 1188 samples
algebra/dev_sup: 834 samples
algebra/dev_ppo_sampled: 558 samples
algebra/test_sup: 1779 samples
algebra/test_ppo_sampled: 1188 samples
prealgebra/train_sup: 1305 samples
prealgebra/train_ppo_sampled: 872 samples
prealgebra/dev_sup: 501 samples
prealgebra/dev_ppo_sampled: 334 samples
prealgebra/test_sup: 1305 samples
prealgebra/test_ppo_sampled: 872 samples
intermediate_algebra/train_sup: 1353 samples
intermediate_algebra/train_ppo_sampled: 904 samples
intermediate_algebra/dev_sup: 588 samples
intermediate_algebra/dev_ppo_sampled: 392 samples
intermediate_algebra/test_sup: 1353 samples
intermediate_algebra/test_ppo_sampled: 904 samples
```

file location format: {task}/{subset}_{mode}.jsonl

## PPO-only training

tasks: algebra_ppo_only, intermediate_algebra_ppo_only, prealgebra_ppo_only
subset: dev, test, train
mode: ppo_sampled
number of samples:
```
algebra_ppo_only/train_ppo_sampled: 2374 samples
algebra_ppo_only/dev_ppo_sampled: 1114 samples
algebra_ppo_only/test_ppo_sampled: 2374 samples
prealgebra_ppo_only/train_ppo_sampled: 1742 samples
prealgebra_ppo_only/dev_ppo_sampled: 668 samples
prealgebra_ppo_only/test_ppo_sampled: 1742 samples
intermediate_algebra_ppo_only/train_ppo_sampled: 1806 samples
intermediate_algebra_ppo_only/dev_ppo_sampled: 784 samples
intermediate_algebra_ppo_only/test_ppo_sampled: 1806 samples
```

file location format: {task}/{subset}_{mode}.jsonl