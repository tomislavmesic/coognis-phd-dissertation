import warnings

DIMENSION_LABELS = {
    "EI": ("E", "I"),
    "SN": ("S", "N"),
    "TF": ("T", "F"),
    "JP": ("J", "P"),
}

class SynapsePredictor:
    def __init__(self, registry, preprocessor):
        self.registry = registry
        self.preprocessor = preprocessor

    def predict(self, text: str):
        text = self.preprocessor.normalize(text)
        features = self._build_features(text)
        results = {}

        for key in DIMENSION_LABELS:
            model = self.registry.get_model(key)
            pred = self._predict_with_known_feature_warning_suppressed(model, features)[0]
            neg, pos = DIMENSION_LABELS[key]

            if hasattr(model, "predict_proba"):
                probs = self._predict_proba_with_known_feature_warning_suppressed(model, features)[0]
                prob = {neg: float(probs[0]), pos: float(probs[1])}
            else:
                prob = {neg: 0.5, pos: 0.5}

            results[key] = {
                "label": pos if pred == 1 else neg,
                "probabilities": prob
            }

        mbti = "".join(results[k]["label"] for k in ["EI","SN","TF","JP"])
        confidence = sum(max(v["probabilities"].values()) for v in results.values()) / 4

        return {
            "mbti_type": mbti,
            "dimensions": results,
            "confidence": confidence,
            "model_version": self.registry.model_version,
            "profile_status": "stable"
        }

    def _build_features(self, text: str):
        vectorizer = self.registry.get_vectorizer()
        tfidf_transformer = self.registry.get_tfidf_transformer()
        self.registry.get_feature_names()

        token_counts = vectorizer.transform([text])
        tfidf_features = tfidf_transformer.transform(token_counts)
        if hasattr(tfidf_features, "toarray"):
            return tfidf_features.toarray()
        return tfidf_features

    @staticmethod
    def _predict_with_known_feature_warning_suppressed(model, features):
        with warnings.catch_warnings():
            warnings.filterwarnings(
                "ignore",
                message=r"X does not have valid feature names, but .* was fitted with feature names",
                category=UserWarning,
            )
            return model.predict(features)

    @staticmethod
    def _predict_proba_with_known_feature_warning_suppressed(model, features):
        with warnings.catch_warnings():
            warnings.filterwarnings(
                "ignore",
                message=r"X does not have valid feature names, but .* was fitted with feature names",
                category=UserWarning,
            )
            return model.predict_proba(features)
