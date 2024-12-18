#!/bin/bash -l
set -x
# Make sure to edit:
# - model_name in config yml file in config_path to point to the ../model folder.
#   or if using checkpoint to t5large_openai_summ_QMQ3V
# - data file paths in rl4lms/data_pools/custom_text_generation_pools.py
# - prompt_path (x2) in config file to point to the ../prompts_edit_numeric.txt
# - cache_path (x2) for storing generations in config file.

WANDB_KEY=$(<wandb_key)

BASE_PATH="./summ_output"
PROJECT_NAME="base-perf"
EXPERIMENT_NAME="t5large_lr5e7_pet_continual"


mkdir -p $BASE_PATH/$PROJECT_NAME/$EXPERIMENT_NAME

# train_text_generation, eval_text_generation
WANDB_API_KEY=$WANDB_KEY python scripts/training/eval_text_generation.py \
--config_path scripts/training/task_configs/openai_summ/t5large_ppo_on_supervised_eval.yml \
--base_path_to_store_results $BASE_PATH \
--project_name $PROJECT_NAME \
--experiment_name $EXPERIMENT_NAME \
--entity_name fisma-korea-advanced-institute-of-science-and-technology \
--log_to_wandb > $BASE_PATH/$PROJECT_NAME/$EXPERIMENT_NAME/eval.out 2>&1
# --log_to_wandb > $BASE_PATH/$PROJECT_NAME/$EXPERIMENT_NAME/log.out 2>&1