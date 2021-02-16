python -m hypothesis.bin.ratio_estimation.train \
    --batch-size 2048 \
    --epochs 25 \
    --lr 0.001 \
    --show \
    --no-logits \
    --hooks "hooks.add_hooks" \
    --lrsched-on-plateau \
    --conservativeness 0.001 \
    --data-test "ratio_estimation.DatasetTest" \
    --data-train "ratio_estimation.DatasetTrain" \
    --estimator "ratio_estimation.RatioEstimator"
