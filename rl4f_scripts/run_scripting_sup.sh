#!/bin/bash -l

WANDB_KEY=$(<wandb_key)

BASE_PATH="./interscript_output"
PROJECT_NAME="interscript_sup_scale"
EXPERIMENT_NAME="t5large_bs6_wd0.01_lr1e-5_beam5_min5_max_100_seed0"
EXPERIMENT_FOLDER=$BASE_PATH/$PROJECT_NAME/$EXPERIMENT_NAME

mkdir -p $EXPERIMENT_FOLDER

WANDB_API_KEY=$WANDB_KEY python scripts/training/train_text_generation.py \
--config_path scripts/training/task_configs/scripting/t5_supervised_large.yaml \
--base_path_to_store_results $BASE_PATH \
--project_name $PROJECT_NAME \
--experiment_name $EXPERIMENT_NAME \
--entity_name fisma-korea-advanced-institute-of-science-and-technology \
--log_to_wandb #> $EXPERIMENT_FOLDER/log.out 2>&1

