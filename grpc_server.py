# grpc_server.py
import grpc
from concurrent import futures
import lightgbm as lgb
import tensorflow as tf
import numpy as np
import feed_ranker_pb2, feed_ranker_pb2_grpc

LAMBDA_MODEL_PATH = "lambdamart.txt"
CTR_MODEL_PATH    = "deepctr_model"

class FeedRankerServicer(feed_ranker_pb2_grpc.FeedRankerServicer):
    def __init__(self):
        self.lm = lgb.Booster(model_file=LAMBDA_MODEL_PATH)
        self.ctr = tf.keras.models.load_model(CTR_MODEL_PATH)

    def Rank(self, request, context):
        items = request.item_ids
        # build feature matrix for each item
        X = []
        for item in items:
            imp = request.context_features.get("impressions", 1.0)
            hr  = request.context_features.get("hour_of_day", 0.0)
            X.append([imp, hr])
        X = np.array(X)
        # score with both models and combine
        score_lm  = self.lm.predict(X)
        score_ctr = self.ctr.predict(X).flatten()
        scores = 0.5*score_lm + 0.5*score_ctr

        # sort
        ranked = sorted(zip(items, scores), key=lambda x: x[1], reverse=True)
        response = feed_ranker_pb2.RankResponse()
        for iid, sc in ranked:
            response.ranked_items.add(item_id=iid, score=float(sc))
        return response

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    feed_ranker_pb2_grpc.add_FeedRankerServicer_to_server(FeedRankerServicer(), server)
    server.add_insecure_port("[::]:50051")
    server.start()
    print("gRPC server running on :50051")
    server.wait_for_termination()

if __name__ == "__main__":
    serve()
