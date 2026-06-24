from fastapi import HTTPException, status

class CaseNotFound(HTTPException):
    def __init__(self, case_id: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Case {case_id} not found"
        )

class EvidenceNotFound(HTTPException):
    def __init__(self, evidence_id: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Evidence {evidence_id} not found"
        )

class FileTooLarge(HTTPException):
    def __init__(self, max_mb: int):
        super().__init__(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds maximum size of {max_mb}MB"
        )

class InvalidFileType(HTTPException):
    def __init__(self, filename: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type not supported: {filename}"
        )