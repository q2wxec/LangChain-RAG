from langchain.text_splitter import CharacterTextSplitter
from langchain.text_splitter import RecursiveCharacterTextSplitter
from typing import List
from langdetect import detect

from config.model_config import SENTENCE_SIZE


class ChineseTextSplitter(RecursiveCharacterTextSplitter):
    def __init__(self, pdf: bool = False, sentence_size: int = SENTENCE_SIZE, **kwargs):
        super().__init__(**kwargs)
        self.pdf = pdf
        self.sentence_size = sentence_size

    def split_text(self, text: str) -> List[str]:   ##此处需要进一步优化逻辑
        chunk_size=self.sentence_size
        # detected_lang = detect(text)
        # if detected_lang != "zh" and detected_lang != "zh-cn":
        #     chunk_size=chunk_size*5
        text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
            # Set a really small chunk size, just to show.
            separators=["\n\n","!","?","。","！","？",";","；",",","，","\n"],
            chunk_size=chunk_size,
            chunk_overlap=0,
            model_name='gpt-3.5-turbo'
            #length_function=len,
            #is_separator_regex=False,
        )
        return text_splitter.split_text(text)
