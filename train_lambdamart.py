# train_lambdamart.py
import lightgbm as lgb
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import ndcg_score

def load_data(path):
    df = pd.read_parquet(path)
    X = df[["impressions", "avg_hour"]]  # add any other features
    y = df["ctr"]
    # group/query grouping key for ranking
    qid = df["user_id"].astype(str) + "_" + df["session_id"].astype(str)
    return X, y, qid

def main(feat_path, model_out):
    X, y, qid = load_data(feat_path)
    X_train, X_val, y_train, y_val, qid_train, qid_val = train_test_split(
        X, y, qid, test_size=0.2, random_state=42
    )

    train_data = lgb.Dataset(X_train, label=y_train, group=qid_train.groupby(qid_train).size().to_list())
    val_data   = lgb.Dataset(X_val, label=y_val, group=qid_val.groupby(qid_val).size().to_list())

    params = {
        "objective": "lambdarank",
        "metric": "ndcg",
        "ndcg_eval_at": [5, 10],
        "learning_rate": 0.05,
        "num_leaves": 31,
        "min_data_in_leaf": 20,
        "boosting": "gbdt"
    }

    bst = lgb.train(
        params,
        train_data,
        valid_sets=[val_data],
        early_stopping_rounds=50,
        num_boost_round=1000
    )

    bst.save_model(model_out)
    print("Saved LambdaMART model to", model_out)

    # quick offline ndcg
    y_pred = bst.predict(X_val)
    ndcg = ndcg_score([y_val.values], [y_pred], k=10)
    print(f"Validation NDCG@10: {ndcg:.4f}")

if __name__ == "__main__":
    import sys
    if len(sys.argv)!=3:
        print("Usage: train_lambdamart.py <features_parquet> <model_out.txt>")
        sys.exit(1)
    main(sys.argv[1], sys.argv[2])
