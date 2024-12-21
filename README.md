# Continual Learning of Critics (CS672 Course Project)

## Introduction to the Codebase

rl4lms library can be downloaded at : [rl4lms-link](https://github.com/allenai/RL4LMs).

necessary data is available at : [data-link](https://drive.google.com/drive/folders/1Rl5j7r8RqvOhQUQPRhK8AEoD5-bjAuDI?usp=sharing).

`scripts/training/task_configs/`: training and evaluation arguments, model and output paths.

`rl4f_scripts/`: script for supervised learning.

`openai_key`: Please specify your API key. (we used gpt-3.5-turbo-instruct)

`wandb_key`: Please specify your API key.


## Running Experiments

All scripts are under `rl4f_scripts`. Specifically, `rl4f_scripts/run_interscript_sup.sh` is the script for running supervised learning to pretrained T5-large to generate critique for interscript. For PPO training, run `rl4f_scripts/run_alphabetize_ppo.sh`.

## Augmented MATH Dataset

For future research, we have included an augmented version of the 
[MATH dataset](https://arxiv.org/abs/2103.03874). The augmented data
follows the format of the Alphabetization task. See `augment_data.ipynb`
for the exact augmentation method.
For more information, view the [MATH_RL directory](MATH_RL/) in this repository.
