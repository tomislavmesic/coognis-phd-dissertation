import re

class SynapsePreprocessor:
    _whitespace_regex = re.compile(r"\s+")
    _url_regex = re.compile(r"https?://\S+|www\.\S+")

    def normalize(self, text: str) -> str:
        text = text.strip()
        text = self._url_regex.sub(" ", text)
        text = text.replace("\n", " ").replace("\r", " ")
        text = self._whitespace_regex.sub(" ", text)
        return text

    def token_count(self, text: str) -> int:
        normalized = self.normalize(text)
        return len(normalized.split()) if normalized else 0
