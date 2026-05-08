from enum import Enum


class MaskingAlgorithm(str, Enum):
    SUBSTITUTION = "substitution"
    HASHING = "hashing"
    REDACTION = "redaction"
    NULLIFICATION = "nullification"
    FPE = "fpe"
    PERTURBATION = "perturbation"
