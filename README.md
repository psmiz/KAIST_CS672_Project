# Continual Learning of Critics (CS672 Course Project)

## Introduction to the Codebase

`rl4lms/data_pools/custom_text_generation_pools.py`: This file contains custom dataset loading classes. Make sure to specify the correct data paths in respective classes.

`scripts/training/task_configs/`: Yaml files containing configs are stored under this path. This is where we specify the training and evaluation arguments, model and output paths. 

`rl4f_scripts/`: A sample sh script for supervised critique generation.

`openai_key`: If running RL4F with one of OpenAI models, you need to place your API key in a file and specify the path in config. Give a path to this key in your yaml file. *Note that RL4F runs using openai API might incur significant charges.*

`wandb_key`: We track our runs using wandb, specify your API key here which is used in the sh script.


## Running Experiments

All scripts can be found under `rl4f_scripts`. For example, check out the `rl4f_scripts/run_alphabetize_sup.sh` script for warm-starting a pretrained T5-large for supervised critique generation for alphabetization. Alternatively, you can load the released checkpoint from the above drive link. For PPO training, specify the checkpoint at `scripts/training/task_configs/alphabetize/t5large_ppo_on_supervised.yaml` and run `rl4f_scripts/run_alphabetize_ppo.sh`.

## Augmented MATH Dataset

For future research, we have included an augmented version of the 
[MATH dataset](https://arxiv.org/abs/2103.03874). The augmented data
follows the format of the Alphabetization task.
For more information, view the [MATH_RL directory](MATH_RL/) in this repository.