#!/bin/bash

set -e

function run_cmd {
    echo ""
    echo "${CMD}"
    if [[ `hostname` == "sc.stanford.edu" ]]; then
        sbatch scripts/train/train_juno.sh "${CMD}"
    else
        ${CMD}
    fi
}

function train_scod {
    args=""
    args="${args} --trainer-config ${TRAINER_CONFIG}"
    args="${args} --scod-config ${SCOD_CONFIG}"
    args="${args} --model-checkpoint ${MODEL_CHECKPOINT}"
    args="${args} --model-network ${MODEL_NETWORK}"
    args="${args} --seed 0"

    if [[ $DEBUG -ne 0 ]]; then
        args="${args} --path ${SCOD_OUTPUT_PATH}_debug"
        args="${args} --overwrite"
    else
        args="${args} --path ${SCOD_OUTPUT_PATH}"
    fi

    CMD="python scripts/train/train_scod.py ${args}"
    run_cmd
}

# Setup.
DEBUG=0
output_path="models"

# Experiments.

exp_name="20220727/decoupled_state"
TRAINER_CONFIG="configs/pybox2d/trainers/scod.yaml"
SCOD_CONFIG="configs/pybox2d/scod/scod.yaml"
MODEL_NETWORK="critic"
policy_envs=("pick" "place" "pull")
checkpoints=(
    "final_model"
    "best_model"
    "ckpt_model_50000"
    "ckpt_model_100000"
)

for ckpt in "${checkpoints[@]}"; do
    for policy_env in "${policy_envs[@]}"; do
        MODEL_CHECKPOINT="${output_path}/${exp_name}/${policy_env}/${ckpt}.pt"
        SCOD_OUTPUT_PATH="${output_path}/${exp_name}/${ckpt}/${policy_env}"
        train_scod
    done
done
