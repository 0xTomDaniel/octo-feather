"""Judgment JSON input validation through check-evals, without classifier calls."""

from collections.abc import Callable

from qa_judgment_shape import calibration_shape, catalogue_shape, labels_shape, model_shape


def test_labels_shape(case: Callable[..., None]) -> None:
    case(labels_shape)


def test_calibration_shape(case: Callable[..., None]) -> None:
    case(calibration_shape)


def test_model_shape(case: Callable[..., None]) -> None:
    case(model_shape)


def test_catalogue_shape(case: Callable[..., None]) -> None:
    case(catalogue_shape)
