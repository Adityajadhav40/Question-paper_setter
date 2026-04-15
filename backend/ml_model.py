import logging
from typing import Iterable, List, Optional

import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

from .models import Question


logger = logging.getLogger(__name__)


class QuestionDifficultyPredictor:
    def __init__(self) -> None:
        self.model: Optional[Pipeline] = None

    def train(self, questions: Iterable[Question]) -> None:
        records = list(questions)
        if len(records) < 20:
            logger.warning("Not enough data to train ML model. Falling back to stored difficulty.")
            self.model = None
            return

        rows: List[dict] = []
        labels: List[str] = []
        for question in records:
            rows.append(
                {
                    "department": question.department,
                    "subject": question.subject,
                    "topic": question.topic,
                    "subtopic": question.subtopic,
                    "marks": question.marks,
                    "type": question.type,
                    "semester": question.semester or 0,
                    "bloom_level": question.bloom_level or "Understand",
                    "times_used": question.times_used or 0,
                }
            )
            labels.append(question.difficulty)

        training_frame = pd.DataFrame(rows)
        preprocessor = ColumnTransformer(
            transformers=[
                (
                    "cat",
                    OneHotEncoder(handle_unknown="ignore"),
                    ["department", "subject", "topic", "subtopic", "type", "bloom_level"],
                ),
                ("num", "passthrough", ["marks", "semester", "times_used"]),
            ]
        )

        self.model = Pipeline(
            steps=[
                ("preprocessor", preprocessor),
                ("classifier", RandomForestClassifier(n_estimators=140, random_state=42)),
            ]
        )
        self.model.fit(training_frame, labels)
        logger.info("ML model trained successfully on %s questions.", len(records))

    def predict_difficulty(self, question: Question) -> str:
        if self.model is None:
            return question.difficulty

        features = pd.DataFrame(
            [
                {
                    "department": question.department,
                    "subject": question.subject,
                    "topic": question.topic,
                    "subtopic": question.subtopic,
                    "marks": question.marks,
                    "type": question.type,
                    "semester": question.semester or 0,
                    "bloom_level": question.bloom_level or "Understand",
                    "times_used": question.times_used or 0,
                }
            ]
        )
        return str(self.model.predict(features)[0])


predictor = QuestionDifficultyPredictor()
