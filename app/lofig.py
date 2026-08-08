import os
import sys
import logging
import json
import base64
import random
from functools import lru_cache

VERSION = "1.0.0"

class Config:
    @classmethod
    @lru_cache(maxsize=1)
    def _cfg_path(self):
        cpth = os.path.join(os.path.dirname(__file__), '../config/config.json')
        if not os.path.isdir(os.path.dirname(cpth)):
            os.mkdir(os.path.dirname(cpth))
        return cpth

    @classmethod
    @lru_cache(maxsize=None)
    def all_configs(self):
        cfg_path = self._cfg_path()
        client_defaults = {
            "log_level": "INFO",
            "port": 8777,
            "log_handler": ["file"],
            "update_server": "https://prod.ailyf.cn",
            "upgrade": "auto",
        }
        if not os.path.isfile(cfg_path):
            self.save({"client": client_defaults})
            return {"client": client_defaults}

        allconfigs = None
        with open(cfg_path, 'r') as f:
            allconfigs = json.load(f)

        bsave = False
        if "client" not in allconfigs:
            allconfigs["client"] = client_defaults
            bsave = True
        else:
            for k, v in client_defaults.items():
                if k not in allconfigs['client']:
                    allconfigs['client'][k] = v
                    bsave = True
        if bsave:
            self.save(allconfigs)

        return allconfigs

    @classmethod
    def save(self, cfg):
        cfg_path = self._cfg_path()
        with open(cfg_path, 'w') as f:
            json.dump(cfg, f, indent=4)

    @classmethod
    def simple_encrypt(self, txt):
        r = random.randint(1, 5)
        x = base64.b64encode(txt.encode('utf-8'))
        for i in range(r):
            x = base64.b64encode(x)
        return '*'*r + x.decode('utf-8')

    @classmethod
    def simple_decrypt(self, etxt):
        r = etxt.rfind('*')
        if r == -1:
            return etxt
        etxt = etxt[r+1:]
        x = base64.b64decode(etxt.encode('utf-8'))
        for i in range(r+1):
            x = base64.b64decode(x)
        return x.decode('utf-8')

    @classmethod
    def client_config(self):
        return self.all_configs()['client']

    @classmethod
    def db_config(self):
        cfg = self.all_configs()
        if 'database' not in cfg:
            cfg['database'] = {}
        return cfg['database']

    @classmethod
    def ai_config(self):
        cfg = self.all_configs()
        if 'ai' not in cfg:
            cfg['ai'] = {}
        return cfg['ai']

    @classmethod
    def log_level(self):
        lvl = self.all_configs()['client'].get("log_level", "INFO").upper()
        return logging._nameToLevel[lvl]

    @classmethod
    def log_handler(self):
        handlers = self.all_configs()['client'].get('log_handler', ['file', 'stdout'])
        lhandlers = []
        if 'file' in handlers:
            lg_path = os.path.join(os.path.dirname(__file__), '../logs/fastread.log')
            if not os.path.isdir(os.path.dirname(lg_path)):
                os.mkdir(os.path.dirname(lg_path))
            lhandlers.append(logging.FileHandler(lg_path))
        if any(x in handlers for x in ['stdout', 'console']):
            lhandlers.append(logging.StreamHandler(sys.stdout))
        return lhandlers

    @classmethod
    def real_path(self, path):
        if path.startswith('~'):
            return os.path.expanduser(path)
        if os.path.isfile(path) or os.path.isdir(path):
            return os.path.abspath(path)
        path = os.path.join(os.path.dirname(os.path.dirname(__file__)), path)
        if os.path.isfile(path) or os.path.isdir(path):
            return os.path.abspath(path)
        return path


logging.basicConfig(
    level=Config.log_level(),
    format='%(levelname)s | %(asctime)s-%(filename)s@%(lineno)d<%(name)s> %(message)s',
    handlers=Config.log_handler(),
    force=True
)

logger: logging.Logger = logging.getLogger('fastread')

