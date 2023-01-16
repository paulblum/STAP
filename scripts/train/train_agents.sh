#!/bin/bash

set -e

# GCP_LOGIN="juno-login-lclbjqwy-001"
# GCP_LOGIN="gcp-login-yq0fvtuw-001"

function run_cmd {
    echo ""
    echo "${CMD}"
    if [[ `hostname` == "sc.stanford.edu" ]] || [[ `hostname` == juno* ]]; then
        sbatch scripts/train/train_juno.sh "${CMD}"
    elif [[ `hostname` == "${GCP_LOGIN}" ]]; then
        sbatch scripts/train/train_gcp.sh "${CMD}"
    else
        ${CMD}
    fi
}

function train_policy {
    args=""
    args="${args} --trainer-config ${TRAINER_CONFIG}"
    args="${args} --agent-config ${AGENT_CONFIG}"
    args="${args} --env-config ${ENV_CONFIG}"
    if [ ! -z "${EVAL_ENV_CONFIG}" ]; then
        args="${args} --eval-env-config ${EVAL_ENV_CONFIG}"
    fi
    if [ ! -z "${ENCODER_CHECKPOINT}" ]; then
        args="${args} --encoder-checkpoint ${ENCODER_CHECKPOINT}"
    fi
    args="${args} --seed 0"
    args="${args} ${ENV_KWARGS}"
    if [[ $DEBUG -ne 0 ]]; then
        args="${args} --path ${POLICY_OUTPUT_PATH}_debug"
        args="${args} --overwrite"
        args="${args} --num-pretrain-steps 10"
        args="${args} --num-train-steps 10"
        args="${args} --num-eval-episodes 10"
    else
        args="${args} --path ${POLICY_OUTPUT_PATH}"
        args="${args} --eval-recording-path ${EVAL_RECORDING_PATH}"
    fi

    CMD="python scripts/train/train_policy.py ${args}"
    run_cmd
}

# Setup.
DEBUG=0
output_path="models"
plots_path="plots"

# Experiments.
exp_name="20230113/sac"

# Pybullet.
AGENT_CONFIG="configs/pybullet/agents/single_stage/sac.yaml"
TRAINER_CONFIG="configs/pybullet/trainers/agent_sac.yaml"

POLICY_OUTPUT_PATH="${output_path}/${exp_name}"
EVAL_RECORDING_PATH="${plots_path}/${exp_name}"
ENV_KWARGS="--num-env-processes 4 --num-eval-env-processes 2"
if [[ `hostname` == "sc.stanford.edu" ]] || [[ `hostname` == "${GCP_LOGIN}" ]] || [[ `hostname` == juno* ]]; then
    ENV_KWARGS="${ENV_KWARGS} --gui 0"
fi

ENV_CONFIG="configs/pybullet/envs/t2m/official/primitives/20230113/primitives_rl/pick.yaml"
EVAL_ENV_CONFIG="configs/pybullet/envs/t2m/official/primitives/20230113/primitives_rl/pick_eval.yaml"
train_policy

ENV_CONFIG="configs/pybullet/envs/t2m/official/primitives/20230113/primitives_rl/place.yaml"
EVAL_ENV_CONFIG="configs/pybullet/envs/t2m/official/primitives/20230113/primitives_rl/place_eval.yaml"
train_policy

ENV_CONFIG="configs/pybullet/envs/t2m/official/primitives/20230113/primitives_rl/pull.yaml"
EVAL_ENV_CONFIG="configs/pybullet/envs/t2m/official/primitives/20230113/primitives_rl/pull_eval.yaml"
train_policy

ENV_CONFIG="configs/pybullet/envs/t2m/official/primitives/20230113/primitives_rl/push.yaml"
EVAL_ENV_CONFIG="configs/pybullet/envs/t2m/official/primitives/20230113/primitives_rl/push_eval.yaml"
train_policy