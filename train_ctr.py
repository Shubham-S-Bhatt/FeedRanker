# train_ctr.py
import pandas as pd
from sklearn.model_selection import train_test_split
from tensorflow import keras
from tensorflow.keras import layers

def build_deep_ctr(input_dim):
    inputs = keras.Input(shape=(input_dim,))
    x = layers.Dense(256, activation="relu")(inputs)
    x = layers.Dense(128, activation="relu")(x)
    x = layers.Dense(64, activation="relu")(x)
    output = layers.Dense(1, activation="sigmoid")(x)
    model = keras.Model(inputs, output)
    model.compile(optimizer="adam", loss="binary_crossentropy", metrics=["AUC"])
    return model

def main(feat_path, model_out):
    df = pd.read_parquet(feat_path)
    X = df[["impressions", "avg_hour"]].values
    y = (df["ctr"] > 0).astype(int).values  # classification proxy

    X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.2, random_state=42)

    model = build_deep_ctr(X.shape[1])
    model.fit(X_train, y_train, epochs=5, batch_size=1024, validation_data=(X_val, y_val))
    model.save(model_out)
    print("Saved Deep CTR model to", model_out)

if __name__ == "__main__":
    import sys
    if len(sys.argv)!=3:
        print("Usage: train_ctr.py <features_parquet> <model_dir>")
        sys.exit(1)
    main(sys.argv[1], sys.argv[2])
