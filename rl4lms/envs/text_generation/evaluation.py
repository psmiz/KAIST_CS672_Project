from functools import partial
from typing import Any, Dict, List
import numpy as np

from rl4lms.data_pools.text_generation_pool import Sample
from rl4lms.envs.text_generation.env import TextGenEnv
from rl4lms.envs.text_generation.evaluation_utils import evaluate_on_samples
from rl4lms.envs.text_generation.utils_supervised import evaluate_on_samples as evaluate_supervised
from rl4lms.envs.text_generation.logging_utils import Tracker
from rl4lms.envs.text_generation.registry import (DataPoolRegistry,
                                                   MetricRegistry,
                                                   RewardFunctionRegistry,
                                                   PolicyRegistry,
                                                   AlgorithmRegistry,
                                                   WrapperRegistry)
from rl4lms.envs.text_generation.reward import RewardFunction
from stable_baselines3.common.env_util import make_vec_env
from stable_baselines3.common.vec_env import SubprocVecEnv
from stable_baselines3.common.env_checker import check_env
from transformers import (AutoTokenizer,
                          AutoModelForCausalLM,
                          AutoModelForSeq2SeqLM,
                          Trainer,
                          TrainingArguments,
                          DataCollatorForLanguageModeling,
                          DataCollatorForSeq2Seq)
from rl4lms.envs.text_generation.utils_supervised import (get_datasets_for_causal,
                                                           get_datasets_for_seq2seq,
                                                           tokenize_causal,
                                                           tokenize_seq2seq,
                                                           EvalCallack)
from rl4lms.envs.text_generation.warm_start import TrainerWarmStartMixin
from myutil import ForkedPdb
import ipdb

def build_tokenizer(tokenizer_config: Dict[str, Any]):
    tokenizer = AutoTokenizer.from_pretrained(
        tokenizer_config["model_name"])
    if tokenizer.pad_token is None and tokenizer_config.get("pad_token_as_eos_token", True):
        tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = tokenizer_config.get(
        "padding_side", "left")
    tokenizer.truncation_side = tokenizer_config.get(
        "truncation_side", "left")
    return tokenizer


def build_reward_fn(reward_config: Dict[str, Any]):
    reward_fn = RewardFunctionRegistry.get(reward_config["id"],
                                           reward_config.get("args", {}))
    return reward_fn


def build_metrics(metric_configs: List[Dict[str, Any]]):
    metrics = [MetricRegistry.get(metric_config["id"], metric_config.get("args", {}))
               for metric_config in metric_configs]
    return metrics


def build_datapool(datapool_config: Dict[str, Any]):

    def _get_datapool_by_split(split: str):
        kwargs = datapool_config.get("args", {})
        kwargs["split"] = split
        dp_split = DataPoolRegistry.get(datapool_config["id"], kwargs)
        return dp_split

    train_datapool = _get_datapool_by_split("train")
    val_datapool = _get_datapool_by_split("val")
    test_datapool = _get_datapool_by_split("test")
    
    samples_by_split = {
        "train": [(sample, weight)
                  for sample, weight in train_datapool],
        "val": [sample for sample, _ in val_datapool],
        "test": [sample for sample, _ in test_datapool]
    }

    return samples_by_split


def build_env(env_config: Dict[str, Any],
              reward_fn: RewardFunction,
              tokenizer: AutoTokenizer,
              train_samples: List[Sample]):
    # vectoried env
    env_kwargs = {
        "reward_function": reward_fn,
        "tokenizer": tokenizer,
        "samples": train_samples,
    }
    env_kwargs = {**env_kwargs, **env_config.get("args", {})}
    env = make_vec_env(TextGenEnv,
                       n_envs=env_config.get(
                           "n_envs", 1),
                       vec_env_cls=SubprocVecEnv,
                       env_kwargs=env_kwargs)
    return env


def build_alg(alg_config: Dict[str, Any],
              env: TextGenEnv,
              tracker: Tracker,
              policy_state: Dict[str, Any],
              alg_state: Dict[str, Any]):
    # TBD - move these to a registry once the experimentation is done
    # Also switch to Sb3 algos when possible with minimal code adaptations
    policy_config = alg_config["policy"]
    policy_cls = PolicyRegistry.get(policy_config["id"])
    alg_cls = AlgorithmRegistry.get(alg_config["id"])

    policy_args = policy_config["args"]
    policy_args["state_dict"] = policy_state
    alg_kwargs = {
        "policy": policy_cls,
        "env": env,
        "policy_kwargs": policy_args,
    }
    alg_kwargs = {**alg_kwargs, **alg_config.get("args")}
    wrapper = WrapperRegistry.get(alg_config["id"])
    alg = wrapper(alg_cls, alg_kwargs,
                  alg_config["kl_div"]["coeff"], tracker,
                  alg_config["kl_div"].get("target_kl", None),
                  alg_config["kl_div"].get("norm_reward", False))
    alg.load_from_dict(alg_state)
    return alg


class OnPolicyEval(TrainerWarmStartMixin):
    """
    A generic trainer for training LMs with onpolicy algorithms from SB3
    """

    def __init__(self,
                 tokenizer_config: Dict[str, Any],
                 datapool_config: Dict[str, Any],
                 reward_config: Dict[str, Any],
                 env_config: Dict[str, Any],
                 on_policy_alg_config: Dict[str, Any],
                 train_eval_config: Dict[str, Any],
                 tracker: Tracker = None,
                 experiment_name: str = ''
                 ):
        self._tokenizer_config = tokenizer_config
        self._datapool_config = datapool_config
        self._reward_config = reward_config
        self._env_config = env_config
        self._on_policy_alg_config = on_policy_alg_config
        self._train_eval_config = train_eval_config
        self._tracker = tracker
        self._experiment_name = experiment_name
        self._setup()

    def _setup(self):
        # load trainer state from available previous checkpoint if available
        self.load_trainer_state(self._tracker)

        # build components
        self._tokenizer = build_tokenizer(self._tokenizer_config)
        self._reward_fn = build_reward_fn(self._reward_config)
        self._metrics = build_metrics(
            self._train_eval_config.get("metrics", []))
        self._samples_by_split = build_datapool(
            self._datapool_config)

        self._env = build_env(self._env_config, self._reward_fn,
                              self._tokenizer, self._samples_by_split["train"])
        # check_env(self._env)
        self._alg = build_alg(self._on_policy_alg_config,
                              self._env, self._tracker,
                              self._policy_state_dict,
                              self._alg_state_dict)

        # extract train params
        self._max_episode_length = self._env_config["args"]["max_episode_length"]
        self._max_prompt_length = self._env_config["args"]["max_prompt_length"]
        self._eval_batch_size = self._train_eval_config["eval_batch_size"]
        self._n_iters = int(self._train_eval_config["n_iters"])
        self._n_steps_per_iter = self._env.num_envs * self._alg.n_steps

        # gen kwargs for evaluation (if it is different from rollout gen kwargs)
        self._eval_gen_kwargs = self._train_eval_config.get(
            "generation_kwargs", None)

    def _evaluate_on_datapools(self, epoch: int,
                               splits: List[str] = ["val", "test"]):
        for split in splits:
            evaluate_on_samples(policy=self._alg.policy,
                                tokenizer=self._tokenizer,
                                samples=self._samples_by_split[split],
                                batch_size=self._eval_batch_size,
                                max_prompt_length=self._max_prompt_length,
                                metrics=self._metrics,
                                epoch=epoch,
                                split_name=split,
                                tracker=self._tracker,
                                gen_kwargs=self._eval_gen_kwargs)

    def eval(self):
        # evaluate on val and test set before fine-tuning once
        iter_start = self._trainer_state["current_iter"]
        self._evaluate_on_datapools(epoch=iter_start)


class SupervisedEval:
    """
    A supervised trainer to train LMs (causal and seq2seq) on text generation tasks (wrapper on HF trainer)
    """

    def __init__(self,
                 tokenizer_config: Dict[str, Any],
                 datapool_config: Dict[str, Any],
                 train_eval_config: Dict[str, Any],
                 alg_config: Dict[str, Any],
                 tracker: Tracker = None
                 ):
        self._tokenizer_config = tokenizer_config
        self._datapool_config = datapool_config
        self._train_eval_config = train_eval_config
        self._alg_config = alg_config
        self._tracker = tracker
        self._setup()

    def _evaluate_on_datapools(self, epoch: int,
                               splits: List[str] = ["val", "test"]):
        for split in splits:
            evaluate_supervised(model=self._model,
                                tokenizer=self._tokenizer,
                                samples=self._samples_by_split[split],
                                batch_size=self._eval_batch_size,
                                max_prompt_length=self._max_prompt_length,
                                metrics_config_dict=self._metrics_config_dict,
                                epoch=epoch,
                                split_name=split,
                                tracker=self._tracker,
                                generation_kwargs=self._gen_kwargs
                                )

    def _setup(self):
        self._tokenizer = build_tokenizer(self._tokenizer_config)
        self._metrics_config_dict = self._train_eval_config.get("metrics")
        self._samples_by_split = build_datapool(
            self._datapool_config)
        self._train_dataset = get_datasets_for_causal(
            self._samples_by_split["train"]) if self._alg_config[
            "model_type"] == "causal" else get_datasets_for_seq2seq(self._samples_by_split["train"])
        preprocess_fn = tokenize_causal if self._alg_config[
            "model_type"] == "causal" else tokenize_seq2seq
        preprocess_fn = partial(preprocess_fn, tokenizer=self._tokenizer)
        self._tokenized_dataset = self._train_dataset.map(
            preprocess_fn, batched=True,
            remove_columns=self._train_dataset.column_names)
        model_cls = AutoModelForCausalLM if self._alg_config[
            "model_type"] == "causal" else AutoModelForSeq2SeqLM
        self._gen_kwargs = self._alg_config["generation_kwargs"]
        self._model = model_cls.from_pretrained(self._alg_config["model_name"])
        # self._model = model_cls.from_pretrained("/home/user/psm/KAIST_CS672_Project/feedback/alphabetize_output/rl4f_alphabetize_sup/t5large_bs32_wd0.01_lr1e-5_beam5_min5_max_20_seed0/model")
        self._model.parallelize()
        self._eval_batch_size = self._train_eval_config["eval_batch_size"]

        # setting max prompt length
        self._max_prompt_length = self._tokenizer_config.get(
            "max_length",  self._tokenizer.model_max_length)

        if (self._alg_config["model_type"] == "causal") and ((self._max_prompt_length + self._gen_kwargs["max_new_tokens"]) > self._tokenizer.model_max_length):
            self._max_prompt_length = self._max_prompt_length - \
                self._gen_kwargs["max_new_tokens"]

        self._eval_callback = EvalCallack(self._samples_by_split["val"],
                                          self._gen_kwargs,
                                          self._eval_batch_size,
                                          self._tokenizer,
                                          self._metrics_config_dict,
                                          self._max_prompt_length,
                                          self._tracker)
    def eval(self):
        # evaluate on val and test set before fine-tuning once
        self._evaluate_on_datapools(epoch=0)