class EcoConfigError(Exception):
    def __init__(self, file_name: str, field_path: str, message: str, suggestion: str | None = None):
        detail = f"[{file_name}] {field_path}: {message}"
        if suggestion:
            detail = f"{detail}. Suggestion: {suggestion}"
        super().__init__(detail)
        self.file_name = file_name
        self.field_path = field_path
        self.message = message
        self.suggestion = suggestion
