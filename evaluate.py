# evaluate.py
import lightgbm as lgb
import numpy as np
import pandas as pd
from sklearn.metrics import ndcg_score
import tensorflow as tf

def eval_lambdamart(model_path, feat_path):
    df = pd.read_parquet(feat_path)
    X = df[["impressions", "avg_hour"]]
    y = df["ctr"]
    bst = lgb.Booster(model_file=model_path)
    y_pred = bst.predict(X)
    return ndcg_score([y.values], [y_pred], k=10)

def eval_ctr(model_dir, feat_path):
    model = tf.keras.models.load_model(model_dir)
    df = pd.read_parquet(feat_path)
    X = df[["impressions", "avg_hour"]].values
    # treat predicted probabilities as scores
    y_pred = model.predict(X).flatten()
    # use ctr as target relevance
    y_true = df["ctr"].values
    return ndcg_score([y_true], [y_pred], k=10)

if __name__=="__main__":
    import sys
    lm_ndcg = eval_lambdamart(sys.argv[1], sys.argv[2])
    ctr_ndcg = eval_ctr(sys.argv[3], sys.argv[2])
    print(f"LambdaMART NDCG@10: {lm_ndcg:.4f}")
    print(f"DeepCTR  NDCG@10: {ctr_ndcg:.4f}")
