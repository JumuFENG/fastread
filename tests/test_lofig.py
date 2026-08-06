#!/usr/bin/env python3
"""
测试lofig.Config的simple_encrypt/simple_decrypt
"""

import os
import sys
import random
import base64
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app.lofig import Config


def test_roundtrip():
    """加解密往返，覆盖不同星号数(1~5)与多种文本"""
    payloads = ["", "hello", "秘密: 你好世界", "a" * 500]
    for seed in range(1, 6):
        random.seed(seed)
        for text in payloads:
            enc = Config.simple_encrypt(text)
            stars = enc.rfind('*') + 1
            assert Config.simple_decrypt(enc) == text, (stars, text)
            print(f"{stars}个* 往返 OK: {text[:15]!r}...")


def test_body_is_clean_base64():
    """回归测试：etxt[r+1:] 后密文主体必须是不含*的合法base64"""
    random.seed(3)
    enc = Config.simple_encrypt("回归测试")
    r = enc.rfind('*')
    body = enc[r+1:]
    base64.b64decode(body.encode('utf-8'), validate=True)


def test_no_star_passthrough():
    """无*前缀的字符串原样返回"""
    assert Config.simple_decrypt("plaintext") == "plaintext"


if __name__ == "__main__":
    test_roundtrip()
    test_body_is_clean_base64()
    test_no_star_passthrough()
    print("所有lofig加密测试通过")
